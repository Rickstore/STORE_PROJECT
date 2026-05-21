from django.db import models
from django.conf import settings
from apps.catalog.models import Product, ProductVariant, Store
import uuid


class Order(models.Model):
    STATUT_CHOICES = (
        ('en_attente', 'En attente'),
        ('valide', 'Payée'),
        ('expedie', 'En chemin'),
        ('livre', 'Livrée'),
        ('retrait_valide', 'Retrait Validé'),
        ('annule', 'Annulée'),
    )

    PAY_MODE_CHOICES = (
        ('orange', 'Orange Money'),
        ('mtn', 'MTN MoMo'),
        ('cash', 'Cash à la livraison'),
        ('nelsius', 'Nelsius'),
        ('fashi', 'Fashi'),
    )

    client_id = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='orders', verbose_name="Client")
    mt_total = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Montant Total")
    statut = models.CharField(max_length=20, choices=STATUT_CHOICES, default='en_attente', verbose_name="Statut")
    pay_mode = models.CharField(max_length=20, choices=PAY_MODE_CHOICES, default='cash', verbose_name="Mode de paiement")
    date_com = models.DateTimeField(auto_now_add=True, verbose_name="Date de commande")
    delivery_code = models.CharField(max_length=6, blank=True, null=True, verbose_name="Code de Livraison")
    order_number = models.CharField(max_length=50, unique=True, editable=False)
    store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders', verbose_name="Boutique")

    class Meta:
        verbose_name = "Commande"
        verbose_name_plural = "Commandes"
        ordering = ['-date_com']

    def __str__(self):
        return f"Commande {self.order_number}"

    def save(self, *args, **kwargs):
        if not self.order_number:
            uid = uuid.uuid4().hex.upper()
            self.order_number = f"CMD-{uid[:8]}"
        # delivery_code is only generated for home deliveries, handled in OrderService
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.RESTRICT, related_name='order_items')
    # FK vers la variante choisie (nullable pour compatibilité avec les anciennes commandes)
    variant = models.ForeignKey(
        ProductVariant,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='order_items',
        verbose_name="Variante"
    )
    price = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Prix unitaire")
    quantity = models.PositiveIntegerField(default=1, verbose_name="Quantité")
    # Gardés pour l'historique lisible (même si la variante est supprimée)
    color = models.CharField(max_length=50, blank=True, null=True, verbose_name="Couleur choisie")
    capacity = models.CharField(max_length=50, blank=True, null=True, verbose_name="Capacité choisie")

    def __str__(self):
        variant_label = f" ({self.color}/{self.capacity})" if (self.color or self.capacity) else ""
        return f"{self.quantity}x {self.product.nom_prod}{variant_label}"

    def get_cost(self):
        return self.price * self.quantity
