from django.db import models
from django.conf import settings
from apps.orders.models import Order

class Delivery(models.Model):
    com_id = models.OneToOneField(Order, on_delete=models.CASCADE, related_name='delivery', verbose_name="Commande")
    livreur_id = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        limit_choices_to={'role': 'livreur'},
        related_name='deliveries',  
        verbose_name="Livreur"
    )
    VILLE_CHOICES = (
        ('douala', 'Douala'),
        ('yaounde', 'Yaoundé'),
    )
    ville_liv = models.CharField(max_length=50, choices=VILLE_CHOICES, verbose_name="Ville de livraison")
    adr_prec = models.TextField(verbose_name="Adresse précise")
    date_fin = models.DateTimeField(blank=True, null=True, verbose_name="Date de fin de livraison")

    class Meta:
        verbose_name = "Livraison"
        verbose_name_plural = "Livraisons"

    def __str__(self):
        return f"Livraison {self.com_id.order_number} - {self.get_ville_liv_display()}"

# Keep LivreurProfile just in case it's used elsewhere for its vehicle_type
class LivreurProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='livreur_profile')
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville (Zone de livraison)")
    vehicle_type = models.CharField(max_length=50, blank=True, verbose_name="Type de véhicule (Ex: Moto, Camionnette)")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")

    def __str__(self):
        return f"Profil Livreur: {self.user.username}"
