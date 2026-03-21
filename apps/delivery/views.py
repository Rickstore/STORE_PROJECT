from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, View
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages
from apps.orders.models import Order
from apps.orders.services import OrderService
from .models import LivreurProfile
from .forms import LivreurProfileForm

class LivreurRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.role == 'livreur'

class DeliveryDashboardView(LivreurRequiredMixin, ListView):
    model = Order
    template_name = 'delivery/dashboard.html'
    context_object_name = 'orders'

    def get_queryset(self):
        # Restriction stricte : afficher seulement les commandes assignées à CE livreur
        # dont le statut est 'assigné' ou 'en cours de livraison'
        return Order.objects.filter(
            assigned_delivery=self.request.user,
            delivery_type='delivery',
            status__in=['assigned', 'delivering']
        ).select_related('address', 'user')

class DeliveryDetailView(LivreurRequiredMixin, DetailView):
    model = Order
    template_name = 'delivery/detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_queryset(self):
        # Restriction stricte aux commandes assignées uniquement
        return Order.objects.filter(
            assigned_delivery=self.request.user,
            delivery_type='delivery'
        ).select_related('address', 'user').prefetch_related('items__product')

class ConfirmDeliveryView(LivreurRequiredMixin, View):
    def post(self, request, order_number):
        order = get_object_or_404(
            Order, 
            order_number=order_number, 
            assigned_delivery=request.user, 
            delivery_type='delivery'
        )
        
        otp = request.POST.get('otp')
        
        # Valider le code à 4 chiffres avec le delivery_code de la commande
        if not otp or otp != order.delivery_code:
            messages.error(request, "Le code de confirmation à 4 chiffres est incorrect.")
            return redirect('delivery:order_detail', order_number=order.order_number)

        try:
            # Mettre à jour le statut de la commande en 'livré'
            OrderService.update_order_status(order, 'delivered', request.user)
            messages.success(request, f"La livraison de la commande {order.order_number} a été confirmée avec succès.")
        except Exception as e:
            messages.error(request, f"Erreur lors de la confirmation: {str(e)}")
            
        return redirect('delivery:dashboard')

class ChangeDeliveryStatusView(LivreurRequiredMixin, View):
    def post(self, request, order_number):
        order = get_object_or_404(
            Order, 
            order_number=order_number, 
            assigned_delivery=request.user, 
            delivery_type='delivery'
        )
        
        new_status = request.POST.get('status')
        delivery_notes = request.POST.get('delivery_notes', '')

        if new_status not in ['delivering', 'failed']:
            messages.error(request, "Statut invalide pour cette action.")
            return redirect('delivery:order_detail', order_number=order.order_number)

        try:
            if delivery_notes.strip():
                order.delivery_notes = delivery_notes
            
            OrderService.update_order_status(order, new_status, request.user)
            messages.success(request, f"Le statut de la commande est passé à : {order.get_status_display()}")
        except Exception as e:
            messages.error(request, f"Erreur : {str(e)}")
            
        if new_status == 'delivering':
            return redirect('delivery:order_detail', order_number=order.order_number)
        return redirect('delivery:dashboard')

class ReportIncidentView(LivreurRequiredMixin, View):
    def post(self, request, order_number):
        order = get_object_or_404(Order, order_number=order_number, assigned_delivery=request.user)
        incident_type = request.POST.get('incident_type')
        details = request.POST.get('details', '')

        # Construire la note d'incident
        incident_note = f"INCIDENT [{incident_type}]: {details}"
        order.delivery_notes = f"{order.delivery_notes}\n{incident_note}" if order.delivery_notes else incident_note
        order.status = 'failed'
        order.save()
        
        messages.warning(request, f"Incident signalé pour la commande {order.order_number}.")
        return redirect('delivery:dashboard')

class LivreurProfileView(LivreurRequiredMixin, View):
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
    """
    Forces a livreur to change their password on first login.
    Only accessible if must_change_password is True, otherwise redirects to dashboard.
    """
    login_url = '/auth/login/'

    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('users:login')
        # If they already changed their password — no need to be here
        if not request.user.must_change_password:
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
        user.must_change_password = False
        user.save()

        # Keep the user logged in after password change
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(request, user)

        messages.success(request, "Votre mot de passe a été changé avec succès. Bienvenue !")
        return redirect('delivery:dashboard')
