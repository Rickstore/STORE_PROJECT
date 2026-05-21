import os
import hmac
import hashlib
import logging
import requests

logger = logging.getLogger(__name__)

class NelsiusService:
    # Service de paiement Nelsius Pay.
    # Réécrit pour utiliser les bonnes URL et clés selon la documentation.

    def __init__(self):
        # Utiliser la clé privée pour l'autorisation Backend-to-Backend
        self.private_key = os.environ.get('NELSIUS_PRIVATE_KEY', '')
        self.public_key = os.environ.get('NELSIUS_PUBLIC_KEY', '') # Optionnel, pour le frontend si besoin
        self.simulation_mode = not self.private_key
        if self.simulation_mode:
            logger.info("[NelsiusPay] Mode SIMULATION activé (aucune clé secrète configurée).")

    def initiate_payment(self, order, provider, phone_number):
        # Lance un paiement Mobile Money.

        if self.simulation_mode:
            logger.info(
                f"[NelsiusPay SIMULATION] Paiement simulé pour commande "
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

        #  PRODUCTION : appel réel à l'API Nelsius (Direct Charge)
        url = "https://api.nelsius.com/api/v1/charges"
        
        # Le fournisseur (ex: 'orange' ou 'mtn') devient l'opérateur pour 'mobile_money'
        provider_lower = provider.lower()
        operator = provider_lower if provider_lower in ['mtn', 'orange', 'wave'] else 'mtn'

        payload = {
            "amount": int(order.mt_total),
            "currency": "XAF",
            "method": "mobile_money",
            "operator": operator,
            "customer_phone": phone_number,
            "reference": str(order.order_number),
            "description": f"Paiement commande {order.order_number} sur AUDSTOREsarl"
        }
        
        headers = {
            "Authorization": f"Bearer {self.private_key}",
            "Content-Type": "application/json"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            logger.error(f"[NelsiusPay] Erreur HTTP: {e}")
            logger.error(f"[NelsiusPay] Response Body: {e.response.text}")
            raise Exception(f"Erreur lors de l'initiation du paiement: {e}")
        except requests.exceptions.RequestException as e:
            logger.error(f"[NelsiusPay] Erreur de requête: {e}")
            raise Exception(
                "Le service de paiement mobile est temporairement indisponible."
            )

    def verify_webhook_signature(self, request):
        # Vérifie la signature du webhook Nelsius
        if self.simulation_mode:
            return True

        signature_header = request.headers.get('X-Nelsius-Signature')
        if not signature_header:
            return False

        payload = request.body
        expected_signature = hmac.new(
            self.private_key.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature_header, expected_signature)