import random
from django.db import transaction
from .models import Order, OrderItem
from apps.users.models import CustomUser

class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order_from_cart(user, cart, delivery_type, address=None, store=None):
        """
        Crée une commande à partir du panier, déduit le stock et l'enregistre en base.
        """
        if len(cart) == 0:
            raise ValueError("Le panier est vide.")

        # Frais et code de livraison
        delivery_fee = 1000 if delivery_type == 'delivery' else 0
        delivery_code = ''.join([str(random.randint(0, 9)) for _ in range(4)]) if delivery_type == 'delivery' else None

        # Créer la commande
        order = Order.objects.create(
            user=user,
            total=cart.get_total_price() + delivery_fee,
            delivery_type=delivery_type,
            address=address if delivery_type == 'delivery' else None,
            store=store if delivery_type == 'pickup' else None,
            delivery_fee=delivery_fee,
            delivery_code=delivery_code
        )

        # Créer les articles de la commande (sans déduire le stock encore)
        for item in cart:
            product = item['product']
            quantity = item['quantity']
            
            # Vérifier la disponibilité du stock avant d'ajouter
            if product.stock < quantity:
                raise ValueError(f"Stock insuffisant pour {product.name}.")
                
            # Créer le ligne de commande
            OrderItem.objects.create(
                order=order,
                product=product,
                price=item['price'],
                quantity=quantity,
                color=item.get('color'),
                capacity=item.get('capacity')
            )
            
        return order

    @staticmethod
    @transaction.atomic
    def confirm_payment_and_deduct_stock(order):
        """
        Appelée quand le paiement est confirmé avec succès.
        Déduit le stock et met à jour le statut de la commande.
        """
        if order.payment_status == 'paid':
            return order  # Déjà traitée
            
        # Déduire le stock pour tous les articles
        for item in order.items.select_related('product'):
            product = item.product
            # Vérifier à nouveau le stock par sécurité
            if product.stock >= item.quantity:
                product.stock -= item.quantity
                product.save()
            else:
                # Stock insuffisant — on déduit quand même pour indiquer un stock négatif (commande en attente)
                # En production, il faudrait alerter l'admin ou refuser (le paiement est déjà pris !)
                product.stock -= item.quantity
                product.save()
                
        # Mettre à jour les statuts
        order.payment_status = 'paid'
        order.status = 'confirmed'  # Prêt pour l'assignation au livreur
        order.save()
        return order

    @staticmethod
    def assign_delivery_person(order, livreur_id=None):
        """
        Assigne un livreur à une commande.
        """
        if order.delivery_type != 'delivery':
            raise ValueError("Cette commande n'est pas en livraison à domicile.")
            
        if livreur_id:
            try:
                livreur = CustomUser.objects.get(id=livreur_id, role='livreur')
                order.assigned_delivery = livreur
            except CustomUser.DoesNotExist:
                raise ValueError("Livreur invalide.")
        else:
            # Assignation automatique : prend le premier livreur disponible (simpliste)
            livreur = CustomUser.objects.filter(role='livreur', is_active=True).first()
            if livreur:
                order.assigned_delivery = livreur
                
        if order.assigned_delivery:
            order.status = 'assigned'
            
        order.save()
        return order

    @staticmethod
    def update_order_status(order, new_status, user):
        """
        Met à jour le statut d'une commande en appliquant strictement les rôles.
        """
        # Flux du livreur
        if user.role == 'livreur':
            allowed_transitions = {
                'assigned': ['delivering'],
                'delivering': ['delivered', 'failed']
            }
            if order.assigned_delivery != user:
                raise PermissionError("Vous n'êtes pas assigné à cette commande.")
            
            if order.status in allowed_transitions and new_status in allowed_transitions[order.status]:
                order.status = new_status
                # Si la livraison est confirmée, le paiement est considéré comme reçu
                if new_status == 'delivered':
                    order.payment_status = 'paid'
                order.save()
                return order
            else:
                raise ValueError(f"Transition non permise: {order.status} -> {new_status}")
                
        # Les admins peuvent tout faire
        elif user.role == 'admin' or user.is_superuser:
            order.status = new_status
            if new_status == 'delivered':
                order.payment_status = 'paid'
            order.save()
            return order
            
        raise PermissionError("Action non autorisée.")
