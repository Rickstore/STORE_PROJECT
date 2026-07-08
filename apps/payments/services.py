from django.conf import settings
from notchpay import NotchPay
import logging

logger = logging.getLogger(__name__)

class NotchPayService:
    # Service de paiement Notch Pay avec SDK.
    
    def __init__(self):
        self.public_key = settings.NOTCHPAY_PUBLIC_KEY
        self.private_key = settings.NOTCHPAY_PRIVATE_KEY
        self.hash_key = settings.NOTCHPAY_HASH_KEY
        self.simulation_mode = not self.private_key
        
        if not self.simulation_mode:
            self.client = NotchPay(self.private_key)
        else:
            logger.info("[NotchPay] Mode SIMULATION activé.")

    def direct_charge(self, order, provider, phone_number):
        """
        Effectue un paiement direct (Direct Charge) Mobile Money.
        1. Initialise le paiement.
        2. Complète le paiement avec le canal et le téléphone.
        """
        if self.simulation_mode:
            logger.info(
                f"[NotchPay SIMULATION] Paiement direct pour commande "
                f"{order.order_number} | {provider} | {phone_number} | {order.mt_total} XAF"
            )
            from apps.orders.services import OrderService
            OrderService.confirm_payment_and_deduct_stock(order)
            return {
                "success": True,
                "simulation": True,
                "message": "Paiement simulé avec succès.",
            }

        try:
            # 1. Initialisation
            init_payload = {
                "amount": int(order.mt_total),
                "currency": "XAF",
                "customer": {
                    "email": order.client_id.email,
                    "name": f"{order.client_id.first_name} {order.client_id.last_name}" if order.client_id.first_name else order.client_id.email,
                },
                "reference": str(order.order_number),
                "description": f"Paiement commande {order.order_number} sur AUDSTOREsarl",
            }
            
            init_response = self.client.payments.initialize(init_payload)
            reference = getattr(init_response, 'reference', None) or init_response.get('reference')
            
            if not reference:
                raise Exception("Impossible d'obtenir une référence de transaction.")

            # 2. Complétion (Direct Charge)
            # Codes canaux pour le Cameroun : cm.mtn, cm.orange
            channel_code = f"cm.{provider.lower()}" # orange -> cm.orange, mtn -> cm.mtn
            
            import requests # On utilise requests pour le 'complete' car pas forcément exposé dans le SDK de la même façon
            complete_url = f"https://api.notchpay.co/payments/{reference}"
            complete_payload = {
                "channel": channel_code,
                "data": {
                    "phone": phone_number
                }
            }
            headers = {
                "Authorization": f"Bearer {self.private_key}", # Le SDK utilise private_key
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            response = requests.post(complete_url, json=complete_payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            logger.error(f"[NotchPay Direct] Erreur: {e}")
            raise Exception(f"Erreur lors du paiement direct: {e}")

    def initiate_payment(self, order, provider, phone_number):
        """Lance un paiement via Notch Pay (Checkout - avec redirection)."""

        if self.simulation_mode:
            logger.info(
                f"[NotchPay SIMULATION] Paiement simulé pour commande "
                f"{order.order_number} | {provider} | {phone_number} | {order.mt_total} XAF"
            )
            from apps.orders.services import OrderService
            OrderService.confirm_payment_and_deduct_stock(order)
            return {
                "success": True,
                "simulation": True,
                "message": "Paiement simulé avec succès.",
                "reference": order.order_number,
            }

        # PRODUCTION : appel réel via SDK Notch Pay
        try:
            payload = {
                "amount": int(order.mt_total),
                "currency": "XAF",
                "customer": {
                    "email": order.client_id.email,
                    "name": f"{order.client_id.first_name} {order.client_id.last_name}" if order.client_id.first_name else order.client_id.email,
                    "phone": phone_number
                },
                "reference": str(order.order_number),
                "description": f"Paiement commande {order.order_number} sur AUDSTOREsarl",
                # On peut ajouter un callback URL si Notch Pay le propose dans le SDK
            }
            
            response = self.client.payments.initialize(payload)
            return response
            
        except Exception as e:
            logger.error(f"[NotchPay] Erreur lors de l'initialisation: {e}")
            raise Exception(f"Erreur lors de l'initiation du paiement Notch Pay: {e}")

    def verify_webhook_signature(self, request):
        """Vérifie la signature du webhook Notch Pay (SHA256 HMAC)."""
        if self.simulation_mode:
            return True

        # Notch Pay utilise X-Notch-Signature ou X-Notchpay-Signature selon les versions
        signature_header = request.headers.get('X-Notch-Signature') or request.headers.get('X-Notchpay-Signature')
        if not signature_header:
            return False

        payload = request.body
        import hmac
        import hashlib
        
        expected_signature = hmac.new(
            self.hash_key.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature_header, expected_signature)