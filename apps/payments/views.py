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
        status = payload.get('status', '').upper()
        
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
            from apps.payments.models import Payment
            payment, created = Payment.objects.get_or_create(
                com_id=order,
                defaults={'mode_pay': order.pay_mode, 'mt_paye': order.mt_total, 'is_valide': True, 'ref_trans': reference}
            )
            if not payment.is_valide:
                payment.is_valide = True
                payment.save(update_fields=['is_valide'])
            logger.info(f"Order {order.order_number} payment marked as successful via webhook.")

        # 4. Traiter le paiement échoué
        elif status == 'FAILED':
            if order.statut != 'valide': # Si ce n'est pas déjà payé
                order.statut = 'annule'
                order.save(update_fields=['statut'])
                logger.info(f"Order {order.order_number} payment failed via webhook.")

        return JsonResponse({"message": "Webhook processed successfully"}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)

