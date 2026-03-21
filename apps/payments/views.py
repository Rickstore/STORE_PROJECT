import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from apps.orders.models import Order
from apps.orders.services import OrderService
from .services import NelsiusService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def nelsius_webhook(request):
    nelsius_service = NelsiusService()
    
    # 1. Vérification OBLIGATOIRE de la signature de sécurité
    if not nelsius_service.verify_webhook_signature(request):
        logger.warning(f"Webhook signature validation failed from IP: {request.META.get('REMOTE_ADDR')}")
        return JsonResponse({"error": "Invalid signature"}, status=403)

    try:
        payload = json.loads(request.body)
        
        reference = payload.get('reference') # Correspond au order_number
        status = payload.get('status')
        
        if not reference or not status:
            return JsonResponse({"error": "Bad request format"}, status=400)

        # 2. Récupérer la commande
        try:
            order = Order.objects.get(order_number=reference)
        except Order.DoesNotExist:
            logger.error(f"Webhook error: Order {reference} not found.")
            return JsonResponse({"error": "Order not found"}, status=404)

        # 3. Traiter le paiement réussi
        if status == 'SUCCESS':
            # Eviter le double-traitement si déjà payé
            if order.payment_status != 'paid':
                OrderService.confirm_payment_and_deduct_stock(order)
                logger.info(f"Order {order.order_number} payment confirmed and stock deducted via webhook.")

        # 4. Traiter le paiement échoué
        elif status == 'FAILED':
            if order.payment_status != 'paid': # Si ce n'est pas déjà payé
                order.payment_status = 'failed'
                order.status = 'failed'
                order.save()
                logger.info(f"Order {order.order_number} payment failed via webhook.")

        return JsonResponse({"message": "Webhook processed successfully"}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

@login_required
def simulate_payment_success(request, order_number):
    """
    Simulation de paiement réussi pour les tests.
    """
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    if order.payment_status != 'paid':
        OrderService.confirm_payment_and_deduct_stock(order)
        messages.success(request, f"Paiement simulé avec succès pour la commande {order_number} !")
    else:
        messages.info(request, "Cette commande est déjà payée.")
        
    return redirect('orders:order_success', order_number=order.order_number)
