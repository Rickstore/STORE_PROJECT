import os
import hmac
import hashlib
import logging

logger = logging.getLogger(__name__)


class NelsiusService:
    """
    Service de paiement Nelsius Pay.
    En mode SIMULATION : retourne toujours un succès sans appel HTTP réel.
    Pour activer le vrai paiement, décommenter NELSIUS_PUBLIC_KEY et
    NELSIUS_PRIVATE_KEY dans le fichier .env et décommenter le bloc requests.
    """

    def __init__(self):
        self.public_key = os.environ.get('NELSIUS_PUBLIC_KEY', '')
        self.private_key = os.environ.get('NELSIUS_PRIVATE_KEY', '')
        self.simulation_mode = not (self.public_key and self.private_key)
        if self.simulation_mode:
            logger.info("[NelsiusPay] Mode SIMULATION activé (aucune clé API configurée).")

    def initiate_payment(self, order, provider, phone_number):
        """
        Lance un paiement Mobile Money.
        En simulation : marque la commande comme payée directement.
        """
        if self.simulation_mode:
            # --- SIMULATION : pas d'appel réseau ---
            logger.info(
                f"[NelsiusPay SIMULATION] Paiement simulé pour commande "
                f"{order.order_number} | {provider} | {phone_number} | {order.total} XAF"
            )
            # Marquer la commande comme payée en simulation
            order.payment_status = 'paid'
            order.save(update_fields=['payment_status'])
            return {
                "success": True,
                "simulation": True,
                "message": "Paiement simulé avec succès (mode développement).",
                "reference": order.order_number,
            }

        # --- PRODUCTION : appel réel à l'API Nelsius ---
        import requests
        url = "https://api.nelsius.com/v1/payments/initiate"
        payload = {
            "amount": int(order.total),
            "currency": "XAF",
            "provider": provider,
            "phone_number": phone_number,
            "reference": order.order_number,
            "description": f"Paiement commande {order.order_number} sur AUDSTOREsarl"
        }
        headers = {
            "Authorization": f"Bearer {self.public_key}",
            "Content-Type": "application/json"
        }
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()

    def verify_webhook_signature(self, request):
        """
        Vérifie la signature du webhook Nelsius (HMAC SHA-256).
        """
        if self.simulation_mode:
            return True  # En simulation, on accepte tout

        signature_header = request.headers.get('X-Nelsius-Signature')
        if not signature_header:
            return False

        payload = request.body
        expected_signature = hmac.new(
            self.private_key.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature_header)
