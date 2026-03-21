from django.db import models
from django.conf import settings
from apps.catalog.models import Product, Store
from apps.users.models import Address
import uuid

class Order(models.Model):
    STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('confirmed', 'Confirmée'),
        ('assigned', 'Assignée'),
        ('delivering', 'En cours de livraison'),
        ('delivered', 'Livrée'),
        ('failed', 'Échouée'),
    )

    DELIVERY_CHOICES = (
        ('delivery', 'Livraison à domicile'),
        ('pickup', 'Retrait en magasin'),
    )

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'En attente'),
        ('paid', 'Payé'),
        ('failed', 'Échoué'),
    )

    order_number = models.CharField(max_length=50, unique=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', verbose_name="Client")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name="Statut")
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Total")
    
    delivery_type = models.CharField(max_length=20, choices=DELIVERY_CHOICES, verbose_name="Type de livraison")
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Magasin de retrait")
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Adresse de livraison")
    
    assigned_delivery = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'role': 'livreur'},
        related_name='deliveries',
        verbose_name="Livreur assigné"
    )
    delivery_notes = models.TextField(blank=True, null=True, verbose_name="Notes de livraison / Incidents")
    delivery_code = models.CharField(max_length=4, blank=True, null=True, verbose_name="Code de confirmation")
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Frais de livraison")
    
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending', verbose_name="Statut du paiement")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            self.order_number = f"CMD-{uuid.uuid4().hex[:8].upper()}"
        super().save(*args, **kwargs)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.RESTRICT, related_name='order_items')
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Prix unitaire")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    
    # Nouvelles informations pour les variantes
    color = models.CharField(max_length=100, blank=True, null=True, verbose_name="Couleur")
    capacity = models.CharField(max_length=100, blank=True, null=True, verbose_name="Capacité")

    def __str__(self):
        desc = f"{self.quantity}x {self.product.name}"
        if self.color or self.capacity:
            desc += f" ({self.color or ''} {self.capacity or ''})".strip()
        return desc

    def get_cost(self):
        return self.price * self.quantity
