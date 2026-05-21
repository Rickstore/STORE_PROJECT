import random
from django.db import transaction
from .models import Order, OrderItem
from apps.users.models import CustomUser


class OrderService:
    @staticmethod
    @transaction.atomic
    def create_order_from_cart(user, cart, delivery_type, city=None, address_details=None, store=None, provider='cash'):
        """
        Crée une commande à partir du panier, vérifie le stock et l'enregistre en base.
        Le stock est déduit uniquement lors de la confirmation du paiement.
        """
        if len(cart) == 0:
            raise ValueError("Le panier est vide.")

        delivery_fee = 1000 if delivery_type == 'delivery' else 0

        # Déduire la boutique de la commande partir des articles du panier
        order_store = None
        for item in cart:
            if item.get('store'):
                order_store = item['store']
                break

        order = Order.objects.create(
            client_id=user,
            mt_total=cart.get_total_price() + delivery_fee,
            pay_mode=provider,
            statut='en_attente',
            store=order_store
        )

        if delivery_type == 'delivery' and address_details:
            import random
            from apps.delivery.models import Delivery
            city_val = city if city else 'Douala'
            Delivery.objects.create(
                com_id=order,
                ville_liv=city_val,
                adr_prec=address_details
            )
            # Generate delivery code only for home deliveries
            order.delivery_code = str(random.randint(100000, 999999))
            order.save(update_fields=['delivery_code'])

        # Créer les articles de la commande
        for item in cart:
            product = item['product']
            quantity = item['quantity']
            variant = item.get('variant')  # ProductVariant ou None

            # Vérification du stock selon la boutique
            if variant and order_store:
                vs = variant.stocks.filter(store=order_store).first()
                v_stock = vs.quantity if vs else 0
                if v_stock < quantity:
                    raise ValueError(f"Stock insuffisant dans {order_store.name} pour {product.nom_prod} ({variant.label}).")
            elif variant:
                if variant.stock < quantity:
                    raise ValueError(f"Stock insuffisant pour {product.nom_prod} ({variant.label}).")
            else:
                # Fallback : vérifier le stock total du produit
                if product.stock_total < quantity:
                    raise ValueError(f"Stock insuffisant pour {product.nom_prod}.")

            OrderItem.objects.create(
                order=order,
                product=product,
                variant=variant,
                price=item['price'],
                quantity=quantity,
                color=item.get('color') or (variant.couleur if variant else None),
                capacity=item.get('capacity') or (variant.capacite if variant else None),
            )

        return order

    @staticmethod
    @transaction.atomic
    def confirm_payment_and_deduct_stock(order):
        """
        Appelée quand le paiement est confirmé.
        Déduit le stock de la variante choisie et met à jour le statut.
        """
        if order.statut != 'en_attente':
            return order  # Déjà traitée

        for item in order.items.all():
            qty = item.quantity

            if item.variant and order.store:
                # Déduction propre sur la variante et la boutique spécifique
                vs = item.variant.stocks.filter(store=order.store).first()
                if vs:
                    if vs.quantity >= qty:
                        vs.quantity -= qty
                        vs.save(update_fields=['quantity'])
                    else:
                        vs.quantity = 0
                        vs.save(update_fields=['quantity'])
            elif item.variant:
                # Fallback au cas où l'ordre n'aurait pas de boutique (old orders)
                pass
            else:
                # Fallback pour anciens items sans variante : pas de déduction
                pass

        order.statut = 'valide'
        order.save()
        return order

    @staticmethod
    def assign_delivery_person(order, livreur_id=None):
        """Assigne un livreur à une commande."""
        if not hasattr(order, 'delivery'):
            raise ValueError("Cette commande n'est pas en livraison à domicile.")

        if livreur_id:
            try:
                livreur = CustomUser.objects.get(id=livreur_id, role='livreur')
                order.delivery.livreur_id = livreur
            except CustomUser.DoesNotExist:
                raise ValueError("Livreur invalide.")
        else:
            livreur = CustomUser.objects.filter(role='livreur', is_active=True).first()
            if livreur:
                order.delivery.livreur_id = livreur

        if order.delivery.livreur_id:
            order.statut = 'expedie'

        order.delivery.save()
        order.save()
        return order

    @staticmethod
    def update_order_status(order, new_status, user):
        """Met à jour le statut d'une commande en appliquant strictement les rôles."""
        # Flux du livreur
        if user.role == 'livreur':
            allowed_transitions = {
                'expedie': ['livre', 'annule'],
            }
            if not hasattr(order, 'delivery') or order.delivery.livreur_id != user:
                raise PermissionError("Vous n'êtes pas assigné à cette commande.")

            if order.statut in allowed_transitions and new_status in allowed_transitions[order.statut]:
                order.statut = new_status
                order.save()
                return order
            else:
                raise ValueError(f"Transition non permise: {order.statut} -> {new_status}")

        # Les admins peuvent tout faire
        elif user.role == 'admin' or user.is_superuser:
            order.statut = new_status
            order.save()
            return order

        raise PermissionError("Action non autorisée.")
