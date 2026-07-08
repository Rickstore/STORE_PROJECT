from django.db import models
from apps.orders.models import Order

class Payment(models.Model):
    MODE_CHOICES = (
        ('notchpay', 'Notch Pay'),
        ('fashi', 'Fashi'),
        ('cash', 'Cash'), 
    )

    com_id = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments', verbose_name="Commande")
    mode_pay = models.CharField(max_length=20, choices=MODE_CHOICES, default='cash', verbose_name="Mode de paiement")
    ref_trans = models.CharField(max_length=100, blank=True, null=True, verbose_name="Référence de transaction")
    mt_paye = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Montant payé")
    date_pay = models.DateTimeField(auto_now_add=True, verbose_name="Date de paiement")
    is_valide = models.BooleanField(default=False, verbose_name="Est valide")

    class Meta:
        verbose_name = "Paiement"
        verbose_name_plural = "Paiements"
        ordering = ['-date_pay']

    def __str__(self):
        return f"Paiement {self.mt_paye} ({self.get_mode_pay_display()}) - {self.com_id.order_number}"

    def save(self, *args, **kwargs):
        is_new_validation = False
        if self.pk:
            old_payment = Payment.objects.get(pk=self.pk)
            if not old_payment.is_valide and self.is_valide:
                is_new_validation = True
        else:
            if self.is_valide:
                is_new_validation = True

        super().save(*args, **kwargs)

        # Logique métier : Si le paiement est en cash et validé, on ajoute le montant au solde du livreur
        if is_new_validation and self.mode_pay == 'cash':
            if hasattr(self.com_id, 'delivery') and self.com_id.delivery.livreur_id:
                livreur = self.com_id.delivery.livreur_id
                livreur.solde_coll += self.mt_paye
                livreur.save()