from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """Modèle utilisateur personnalisé avec rôles et attributs spécifiques au livreur."""
    ROLE_CHOICES = (
        ('admin', 'Administrateur'),
        ('client', 'Client'),
        ('livreur', 'Livreur'),
    )
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='client')
    phone = models.CharField(max_length=20, blank=True, null=True, verbose_name="Téléphone")
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True, verbose_name="Photo de profil")
    must_reset = models.BooleanField(default=False, verbose_name="Doit réinitialiser son mot de passe", help_text="Cocher pour forcer le changement du mot de passe (ex: '0000')")
    solde_coll = models.DecimalField(max_digits=12, decimal_places=0, default=0, verbose_name="Solde collecté", help_text="Portefeuille cash pour le livreur (montants encaissés)")
    is_dispo = models.BooleanField(default=True, verbose_name="Est disponible", help_text="Indique si le livreur est prêt pour de nouvelles courses")
    ville = models.CharField(max_length=100, blank=True, null=True, verbose_name="Ville")
    adresse = models.TextField(blank=True, null=True, verbose_name="Adresse détaillée")
    
    # Les champs email, username, password, is_active, date_joined sont hérités de AbstractUser
    # Note : date_joined fait office de date de création
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def is_admin_role(self):
        """Vérifie si l'utilisateur a un rôle d'administrateur ou superutilisateur."""
        return self.role == 'admin' or self.is_superuser
    
    @property
    def is_client_role(self):
        return self.role == 'client'
        
    @property
    def is_livreur_role(self):
        return self.role == 'livreur'

    @property
    def requires_password_reset(self):
        """Vérifie si l'utilisateur doit être redirigé vers la page de changement de mot de passe."""
        return self.must_reset

