from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from apps.cart.services import CartService
from .services import OrderService
from apps.users.models import Address
from apps.catalog.models import Store
from apps.payments.services import NelsiusService
from .models import Order

@login_required
def checkout(request):
    cart = CartService(request)
    if len(cart) == 0:
        return redirect('cart:cart_detail')
        
    if request.method == 'POST':
        delivery_type = request.POST.get('delivery_type')
        provider = request.POST.get('provider', 'orange')  # 'orange', 'mtn', or 'cash'
        
        try:
            if delivery_type == 'delivery':
                city = request.POST.get('city')
                address_details = request.POST.get('address')
                phone = request.POST.get('phone')
                
                address = Address.objects.create(
                    user=request.user,
                    city=city,
                    address=address_details,
                    phone=phone
                )
                order = OrderService.create_order_from_cart(
                    user=request.user, cart=cart,
                    delivery_type=delivery_type, address=address
                )
            else:
                store_id = request.POST.get('store_id')
                store = Store.objects.get(id=store_id)
                order = OrderService.create_order_from_cart(
                    user=request.user, cart=cart,
                    delivery_type=delivery_type, store=store
                )

            # Apply delivery fee for home delivery
            if delivery_type == 'delivery':
                order.delivery_fee = 1000
                order.total = order.total + 1000
                order.save()

            # Clear cart
            cart.clear()

            if provider == 'cash':
                # Cash on delivery: no online payment needed
                order.payment_status = 'pending'  # Will be set to 'paid' when livreur confirms
                order.save()
                messages.success(request, "Commande confirmée ! Votre livreur encaissera le paiement à la livraison.")
                return redirect('orders:order_success', order_number=order.order_number)
            else:
                # Initiate Nelsius Pay Payment (Orange Money / MTN)
                phone_for_payment = request.POST.get('payment_phone', '') or request.POST.get('mtn_phone', '') or request.user.phone
                
                nelsius = NelsiusService()
                response = nelsius.initiate_payment(order, provider, phone_for_payment)
                
                messages.success(request, "Commande validée ! Veuillez confirmer le paiement sur votre mobile.")
                return redirect('orders:order_success', order_number=order.order_number)
            
        except Exception as e:
            messages.error(request, f"Erreur lors de la validation: {str(e)}")
            return redirect('orders:checkout')
            
    # GET
    stores = Store.objects.all()
    user_addresses = request.user.addresses.all()
    return render(request, 'orders/checkout.html', {'cart': cart, 'stores': stores, 'addresses': user_addresses})

@login_required
def order_success(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
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
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    # On autorise l'export même si non payé pour le test, mais normalement :
    # if order.payment_status != 'paid': ...
        
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
