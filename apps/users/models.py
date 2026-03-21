from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('client', 'Client'),
        ('livreur', 'Livreur'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Photo de profil")
    must_change_password = models.BooleanField(default=False, verbose_name="Doit changer son mot de passe")
    
    # We already have email, username, password, is_active, date_joined from AbstractUser
    # Note: date_joined serves as created_at
    
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin_role(self):
        return self.role == 'admin' or self.is_superuser
    
    @property
    def is_client_role(self):
        return self.role == 'client'
        
    @property
    def is_livreur_role(self):
        return self.role == 'livreur'

class Address(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='addresses')
    city = models.CharField(max_length=100, verbose_name="Ville")
    address = models.TextField(verbose_name="Adresse détaillée")
    phone = models.CharField(max_length=20, verbose_name="Téléphone")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Adresse"
        verbose_name_plural = "Adresses"
        
    def __str__(self):
        return f"{self.user.username} - {self.city}"
