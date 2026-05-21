from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from django.utils import timezone
from apps.orders.models import Order
from apps.orders.services import OrderService
from .models import LivreurProfile, Delivery
from .forms import LivreurProfileForm
from django.db import transaction
from django.contrib.auth import update_session_auth_hash

class LivreurRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    # Mixin pour restreindre l'accès uniquement aux utilisateurs ayant le rôle 'livreur'.
    login_url = '/auth/login/'

    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'livreur'

    def dispatch(self, request, *args, **kwargs):
        if not self.test_func():
            return self.handle_no_permission()
        # Si le livreur doit réinitialiser son mot de passe, on le redirige
        if getattr(request.user, 'must_reset', False):
            return redirect('delivery:force_change_password')
        return super().dispatch(request, *args, **kwargs)


class DeliveryDashboardView(LivreurRequiredMixin, ListView):
    """Tableau de bord affichant les commandes assignées au livreur connecté."""
    model = Order
    template_name = 'delivery/dashboard.html'
    context_object_name = 'orders'

    def get_queryset(self):
        # Afficher uniquement les commandes assignées à CE livreur avec le statut 'expedie'
        return Order.objects.filter(
            delivery__livreur_id=self.request.user,
            statut='expedie'
        ).select_related('client_id', 'delivery').order_by('-date_com')


class DeliveryDetailView(LivreurRequiredMixin, DetailView):
    """Vue détaillée d'une livraison spécifique."""
    model = Order
    template_name = 'delivery/detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_queryset(self):
        return Order.objects.filter(
            delivery__livreur_id=self.request.user
        ).select_related('client_id', 'delivery').prefetch_related('items__product')


class ConfirmDeliveryView(LivreurRequiredMixin, View):
    """Confirme la livraison d'une commande via la validation du code client."""
    def post(self, request, order_number):
        order = get_object_or_404(
            Order,
            order_number=order_number,
            delivery__livreur_id=request.user,
        )

        delivery_code = request.POST.get('delivery_code')
        # Vérification du code fourni par le client
        if order.delivery_code and (not delivery_code or delivery_code.strip() != order.delivery_code):
            messages.error(request, "Code de livraison incorrect. Veuillez demander le code secret au client.")
            return redirect('delivery:order_detail', order_number=order.order_number)

        try:
            with transaction.atomic():
                # Mise à jour du statut vers 'livre'
                OrderService.update_order_status(order, 'livre', request.user)
                
                if hasattr(order, 'delivery'):
                    order.delivery.date_fin = timezone.now()
                    order.delivery.save(update_fields=['date_fin'])
                
                # Gestion du paiement automatique pour les commandes en cash
                if order.pay_mode == 'cash':
                    from apps.payments.models import Payment
                    # Vérifier s'il y a déjà un paiement initié
                    payment = Payment.objects.filter(com_id=order, mode_pay='cash').first()
                    if payment:
                        payment.is_valide = True
                        payment.mt_paye = order.mt_total
                        payment.save()
                    else:
                        Payment.objects.create(
                            com_id=order,
                            mode_pay='cash',
                            mt_paye=order.mt_total,
                            is_valide=True
                        )
                    # Note : Le modèle Payment met à jour solde_coll via son signal/save()
                    
            messages.success(request, f"La livraison de la commande {order.order_number} a été confirmée avec succès. Votre solde a été mis à jour.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la confirmation : {str(e)}")

        return redirect('delivery:dashboard')

class ChangeDeliveryStatusView(LivreurRequiredMixin, View):
    """Permet au livreur de changer le statut d'une commande (ex: en cours de livraison ou échec)."""
    def post(self, request, order_number):
        order = get_object_or_404(
            Order,
            order_number=order_number,
            delivery__livreur_id=request.user,
        )

        new_status = request.POST.get('status')
        # Correspondance des statuts de l'interface vers le modèle Order
        status_map = {
            'delivering': 'expedie',
            'failed': 'annule',
        }
        mapped_status = status_map.get(new_status)

        if not mapped_status:
            messages.error(request, "Statut invalide pour cette action.")
            return redirect('delivery:order_detail', order_number=order.order_number)

        try:
            OrderService.update_order_status(order, mapped_status, request.user)
            messages.success(request, f"Le statut de la commande est passé à : {order.get_statut_display()}")
        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")

        if mapped_status == 'expedie':
            return redirect('delivery:order_detail', order_number=order.order_number)
        return redirect('delivery:dashboard')

class ReportIncidentView(LivreurRequiredMixin, View):
    """Permet au livreur de signaler un incident et d'annuler la livraison."""
    def post(self, request, order_number):
        order = get_object_or_404(
            Order,
            order_number=order_number,
            delivery__livreur_id=request.user
        )
        incident_type = request.POST.get('incident_type')
        details = request.POST.get('details', '')

        # Marquer la commande comme annulée en cas d'incident
        order.statut = 'annule'
        order.save(update_fields=['statut'])

        messages.warning(request, f"Incident [{incident_type}] signalé pour la commande {order.order_number}.")
        return redirect('delivery:dashboard')

class LivreurProfileView(LivreurRequiredMixin, View):
    """Gère l'affichage et la mise à jour du profil du livreur."""
    def get(self, request):
        profile, created = LivreurProfile.objects.get_or_create(user=request.user)
        form = LivreurProfileForm(instance=profile, user=request.user)
        return render(request, 'delivery/profile.html', {'form': form, 'profile': profile})

    def post(self, request):
        profile, created = LivreurProfile.objects.get_or_create(user=request.user)
        form = LivreurProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Votre profil a été mis à jour avec succès.")
            return redirect('delivery:profile')
        else:
            messages.error(request, "Erreur lors de la mise à jour du profil. Veuillez vérifier les champs.")
        return render(request, 'delivery/profile.html', {'form': form, 'profile': profile})

class ForceChangePasswordView(LoginRequiredMixin, View):
    """Force le livreur à changer son mot de passe lors de sa toute première connexion."""
    login_url = '/auth/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        # Si le mot de passe a déjà été changé, on le redirige vers le tableau de bord
        if not request.user.requires_password_reset:
            return redirect('delivery:dashboard')
        return super().dispatch(request, *args, **kwargs)

    def get(self, request):
        return render(request, 'delivery/force_change_password.html')

    def post(self, request):
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if len(new_password) < 8:
            messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            return render(request, 'delivery/force_change_password.html')

        if new_password != confirm_password:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return render(request, 'delivery/force_change_password.html')

        user = request.user
        user.set_password(new_password)
        user.must_reset = False
        user.save()
        # Maintenir l'utilisateur connecté après le changement de mot de passe
        update_session_auth_hash(request, user)
        messages.success(request, "Votre mot de passe a été changé avec succès. Bienvenue !")
        return redirect('delivery:dashboard')