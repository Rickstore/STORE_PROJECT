from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.cart.services import CartService
from .services import OrderService
from apps.catalog.models import Store
from apps.payments.services import NelsiusService
from .models import Order

@login_required
def checkout(request):
    cart = CartService(request)
    if len(cart) == 0:
        return redirect('cart:cart_detail')
    if request.method == 'POST':
        # Admins ne peuvent pas passer de commandes clients
        if request.user.role == 'admin' or request.user.is_superuser:
            messages.error(request, "Les administrateurs ne peuvent pas valider de commandes clients.")
            return redirect('dashboard:index')

        delivery_type = request.POST.get('delivery_type')
        provider = request.POST.get('provider', 'orange')  # 'orange', 'mtn', or 'cash'
        
        try:
            if delivery_type == 'delivery':
                city = request.POST.get('city')
                address_details = request.POST.get('address')
                phone = request.POST.get('phone')
                
                order = OrderService.create_order_from_cart(
                    user=request.user, cart=cart,
                    delivery_type=delivery_type, city=city, address_details=address_details, provider=provider
                )
            else:
                store_id = request.POST.get('store_id')
                store = Store.objects.get(id=store_id)
                order = OrderService.create_order_from_cart(
                    user=request.user, cart=cart,
                    delivery_type=delivery_type, store=store, provider=provider
                )

            # Clear cart
            cart.clear()

            if provider == 'cash':
                # Cash on delivery: no online payment needed
                messages.success(request, "Commande confirmée ! Votre livreur encaissera le paiement à la livraison.")
                return redirect('orders:order_success', order_number=order.order_number)
            else:
                # Initiate Nelsius Pay Payment (Orange Money / MTN)
                phone_for_payment = (
                    request.POST.get('payment_phone', '').strip()
                    or request.POST.get('mtn_phone', '').strip()
                    or getattr(request.user, 'phone', '')
                )
                if not phone_for_payment:
                    messages.error(request, "Veuillez saisir un numéro de téléphone pour le paiement mobile.")
                    return redirect('orders:checkout')

                import logging
                logger = logging.getLogger(__name__)

                nelsius = NelsiusService()
                try:
                    response = nelsius.initiate_payment(order, provider, phone_for_payment)
                    logger.info(f"[Nelsius] Réponse API pour commande {order.order_number}: {response}")

                    # Vérifier si l'API signale un échec
                    if isinstance(response, dict) and response.get('success') is False:
                        error_msg = response.get('message', 'Erreur inconnue de l\'opérateur.')
                        messages.error(request, f"Paiement refusé par l'opérateur : {error_msg}")
                        return redirect('orders:checkout')

                    messages.success(request, "Commande reçue ! Confirmez le paiement sur votre mobile (prompt USSD). Elle sera validée automatiquement.")
                    return redirect('orders:order_success', order_number=order.order_number)

                except Exception as payment_error:
                    logger.error(f"[Nelsius] Erreur paiement commande {order.order_number}: {payment_error}")
                    messages.error(request, f"Erreur lors de l'initiation du paiement mobile : {payment_error}")
                    return redirect('orders:checkout')

        except Exception as e:
            messages.error(request, f"Erreur lors de la validation: {str(e)}")
            return redirect('orders:checkout')
            
    # GET
    stores = Store.objects.all()
    nelsius = NelsiusService()
    return render(request, 'orders/checkout.html', {
        'cart': cart, 
        'stores': stores,
        'is_sandbox': nelsius.simulation_mode
    })

@login_required
def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, client_id=request.user)
    return render(request, 'orders/success.html', {'order': order})

@login_required
def order_history(request):
    orders = request.user.orders.all()
    return render(request, 'orders/history.html', {'orders': orders})
import io
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html  = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None

@login_required
def export_order_pdf(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, client_id=request.user)
    # On autorise l'export même si non payé pour le test, mais normalement :
    # if order.statut != 'valide': ...
        
    context = {
        'order': order,
        'items': order.items.all(),
        'pagesize': 'A4',
    }
    pdf = render_to_pdf('orders/invoice_pdf.html', context)
    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        filename = f"Facture_{order.order_number}.pdf"
        content = f"attachment; filename={filename}"
        response['Content-Disposition'] = content
        return response
    return HttpResponse("Erreur lors de la génération du PDF", status=500)
