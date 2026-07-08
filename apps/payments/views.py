import json
import logging
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from apps.orders.models import Order
from apps.orders.services import OrderService
from .services import NotchPayService

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def notchpay_webhook(request):
    notchpay_service = NotchPayService()
    
    # 1. Vérification OBLIGATOIRE de la signature de sécurité
    if not notchpay_service.verify_webhook_signature(request):
        logger.warning(f"Webhook signature validation failed from IP: {request.META.get('REMOTE_ADDR')}")
        return JsonResponse({"error": "Invalid signature"}, status=403)

    try:
        payload = json.loads(request.body)
        
        # Structure Notch Pay: { "event": "payment.complete", "data": { "reference": "...", "status": "..." } }
        event = payload.get('event') or payload.get('type') # Notch Pay uses 'type' in some docs
        data = payload.get('data', {})
        
        reference = data.get('reference')
        status = data.get('status', '').upper()
        
        if not reference or not status:
            return JsonResponse({"error": "Bad request format"}, status=400)

        # 2. Récupérer la commande
        try:
            order = Order.objects.get(order_number=reference)
        except Order.DoesNotExist:
            logger.error(f"Webhook error: Order {reference} not found.")
            return JsonResponse({"error": "Order not found"}, status=404)

        # 3. Traiter le paiement réussi
        if (event == 'payment.complete' or event == 'payment.success') and status == 'COMPLETE':
            from apps.payments.models import Payment
            payment, created = Payment.objects.get_or_create(
                com_id=order,
                defaults={'mode_pay': 'notchpay', 'mt_paye': order.mt_total, 'is_valide': True, 'ref_trans': reference}
            )
            if not payment.is_valide:
                payment.is_valide = True
                payment.save(update_fields=['is_valide'])
            
            # Confirmer la commande si ce n'est pas déjà fait
            from apps.orders.services import OrderService
            OrderService.confirm_payment_and_deduct_stock(order)
            
            logger.info(f"Order {order.order_number} payment marked as successful via Notch Pay webhook.")

        # 4. Traiter le paiement échoué
        elif event == 'payment.failed' or status == 'FAILED':
            if order.statut != 'valide':
                order.statut = 'annule'
                order.save(update_fields=['statut'])
                logger.info(f"Order {order.order_number} payment failed via Notch Pay webhook.")

        return JsonResponse({"message": "Webhook processed successfully"}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}")
        return JsonResponse({"error": "Internal server error"}, status=500)

