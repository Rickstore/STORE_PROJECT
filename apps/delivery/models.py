from django.db import models
from django.conf import settings

class LivreurProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='livreur_profile')
    city = models.CharField(max_length=100, blank=True, verbose_name="Ville (Zone de livraison)")
    vehicle_type = models.CharField(max_length=50, blank=True, verbose_name="Type de véhicule (Ex: Moto, Camionnette)")
    is_available = models.BooleanField(default=True, verbose_name="Disponible")

    def __str__(self):
        return f"Profil Livreur: {self.user.username}"
