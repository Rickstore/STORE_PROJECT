from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse
from .models import CustomUser, Address
from .forms import UserUpdateForm
from apps.orders.models import Order
import io


def register_view(request):
    if request.user.is_authenticated:
        return redirect('catalog:home')
        
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        
        if password != password_confirm:
            messages.error(request, "Les mots de passe ne correspondent pas.")
            return redirect('users:register')
            
        if CustomUser.objects.filter(username=username).exists():
            messages.error(request, "Ce nom d'utilisateur est déjà pris.")
            return redirect('users:register')
            
        try:
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                phone=phone,
                role='client'
            )
            login(request, user)
            messages.success(request, f"Bienvenue {username} ! Votre compte a été créé.")
            return redirect('catalog:home')
        except Exception as e:
            messages.error(request, f"Erreur lors de l'inscription : {str(e)}")
            return redirect('users:register')
            
    return render(request, 'users/register.html')


def login_view(request):
    if request.user.is_authenticated:
        return redirect('catalog:home')
        
    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')

        if not email or not password:
            messages.error(request, "Veuillez remplir tous les champs.")
            return render(request, 'users/login.html')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            login(request, user)
            if user.role == 'admin' or user.is_superuser:
                return redirect('dashboard:index')
            elif user.role == 'livreur':
                # Force password change on first login
                if user.must_change_password:
                    return redirect('delivery:force_change_password')
                return redirect('delivery:dashboard')
            else:
                next_url = request.GET.get('next') or '/'
                return redirect(next_url)
        else:
            messages.error(request, "Email ou mot de passe incorrect.")

    return render(request, 'users/login.html')


def logout_view(request):
    logout(request)
    messages.info(request, "Vous avez été déconnecté avec succès.")
    return redirect('catalog:home')


@login_required(login_url='/auth/login/')
def profile_view(request):
    user = request.user
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'update_profile':
            form = UserUpdateForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "Profil mis à jour avec succès.")
            else:
                messages.error(request, "Erreur lors de la mise à jour du profil.")
        elif action == 'change_password':
            current_pw = request.POST.get('current_password')
            new_pw = request.POST.get('new_password')
            confirm_pw = request.POST.get('confirm_password')
            if not user.check_password(current_pw):
                messages.error(request, "Mot de passe actuel incorrect.")
            elif new_pw != confirm_pw:
                messages.error(request, "Les nouveaux mots de passe ne correspondent pas.")
            elif len(new_pw) < 8:
                messages.error(request, "Le mot de passe doit contenir au moins 8 caractères.")
            else:
                user.set_password(new_pw)
                user.save()
                # Re-login after password change
                from django.contrib.auth import update_session_auth_hash
                update_session_auth_hash(request, user)
                messages.success(request, "Mot de passe modifié avec succès.")
        return redirect('users:profile')

    addresses = user.addresses.all()
    orders_count = user.orders.count()
    context = {
        'user': user,
        'addresses': addresses,
        'orders_count': orders_count,
    }
    return render(request, 'users/profile.html', context)


@login_required(login_url='/auth/login/')
def address_create(request):
    if request.method == 'POST':
        city = request.POST.get('city', '').strip()
        address_text = request.POST.get('address', '').strip()
        phone = request.POST.get('phone', '').strip()
        if city and address_text and phone:
            Address.objects.create(
                user=request.user,
                city=city,
                address=address_text,
                phone=phone
            )
            messages.success(request, "Adresse ajoutée.")
        else:
            messages.error(request, "Veuillez remplir tous les champs.")
    return redirect('users:profile')


@login_required(login_url='/auth/login/')
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, "Adresse supprimée.")
    return redirect('users:profile')


@login_required(login_url='/auth/login/')
def order_history_view(request):
    orders = request.user.orders.prefetch_related('items__product').order_by('-created_at')
    return render(request, 'users/order_history.html', {'orders': orders})


@login_required(login_url='/auth/login/')
def order_track_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    # Build a status timeline
    status_steps = ['pending', 'confirmed', 'assigned', 'delivering', 'delivered']
    current_idx = status_steps.index(order.status) if order.status in status_steps else -1
    context = {
        'order': order,
        'status_steps': status_steps,
        'current_idx': current_idx,
    }
    return render(request, 'users/order_track.html', context)


@login_required(login_url='/auth/login/')
def invoice_download(request, order_number):
    """Generate a simple text invoice for the order."""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    
    lines = []
    lines.append("=" * 50)
    lines.append("         FACTURE - AUDSTOREsarl")
    lines.append("=" * 50)
    lines.append(f"Référence    : {order.order_number}")
    lines.append(f"Date         : {order.created_at.strftime('%d/%m/%Y à %H:%M')}")
    lines.append(f"Client       : {order.user.username}")
    lines.append(f"Email        : {order.user.email}")
    lines.append(f"Téléphone    : {order.user.phone or '—'}")
    lines.append("-" * 50)
    lines.append("ARTICLES COMMANDÉS")
    lines.append("-" * 50)
    for item in order.items.all():
        lines.append(f"  {item.product.name}")
        lines.append(f"    {item.quantity} x {item.price:,.0f} FCFA = {item.get_cost():,.0f} FCFA")
    lines.append("-" * 50)
    lines.append(f"  TOTAL             : {order.total:,.0f} FCFA")
    lines.append(f"  Mode de livraison : {order.get_delivery_type_display()}")
    lines.append(f"  Statut paiement   : {order.get_payment_status_display()}")
    lines.append("=" * 50)
    lines.append("   Merci pour votre confiance !")
    lines.append("   AUDSTOREsarl | +237 6 57 29 24 63")
    lines.append("=" * 50)

    content = "\n".join(lines)
    response = HttpResponse(content, content_type='text/plain; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="facture-{order.order_number}.txt"'
    return response
