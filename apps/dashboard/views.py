from django.views.generic import TemplateView, ListView, DetailView, View, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404, render
from django.http import JsonResponse
from apps.orders.models import Order, OrderItem
from apps.catalog.models import Product, ProductVariant, VariantStock, Category, ProductReview
from apps.users.models import CustomUser
from .forms import ProductForm, CategoryForm, LivreurCreationForm, LivreurUpdateForm
from django.urls import reverse_lazy


class AdminRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    login_url = '/auth/login/'

    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    template_name = 'dashboard/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.now().date()

        total_revenue = Order.objects.filter(statut='livre').aggregate(
            total=Sum('mt_total'))['total'] or 0
        total_orders = Order.objects.count()
        orders_today = Order.objects.filter(date_com__date=today).count()
        
        success_deliveries = Order.objects.filter(statut='livre').count()
        avg_cart = (total_revenue / success_deliveries) if success_deliveries > 0 else 0
        low_stock_variant_count = ProductVariant.objects.filter(
            stocks__quantity__lte=5, is_active=True, product__is_active=True
        ).count()
        low_stock_count = low_stock_variant_count
        pending_orders = Order.objects.filter(statut='en_attente').count()
        pending_reviews = ProductReview.objects.filter(is_approved=False).count()

        top_products = OrderItem.objects.filter(
            order__statut='livre'
        ).values('product__marque', 'product__nom_prod').annotate(
            total_sales_value=Sum('price'),
            total_sold=Sum('quantity')
        ).order_by('-total_sales_value')[:4]

        # Calculate sales data for the last 6 months
        import calendar
        months_labels = []
        sales_data = []
        french_months = ['', 'Jan', 'Fév', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Août', 'Sept', 'Oct', 'Nov', 'Déc']
        for i in range(5, -1, -1):
            m = today.month - i
            y = today.year
            if m <= 0:
                m += 12
                y -= 1
            months_labels.append(french_months[m])
            month_sales = Order.objects.filter(
                statut='livre',
                date_com__year=y,
                date_com__month=m
            ).aggregate(total=Sum('mt_total'))['total'] or 0
            sales_data.append(int(month_sales))

        total_deliveries = Order.objects.exclude(statut='en_attente').count()
        success_deliveries = Order.objects.filter(statut='livre').count()
        failed_deliveries = Order.objects.filter(statut='annule').count()
        success_rate = (success_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
        failed_rate = (failed_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
        recent_orders = Order.objects.filter(statut__in=['valide', 'livre']).select_related('client_id').order_by('-date_com')[:6]

        context.update({
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'orders_today': orders_today,
            'avg_cart': avg_cart,
            'low_stock_count': low_stock_count,
            'pending_count': pending_orders,
            'pending_reviews_count': pending_reviews,
            'top_products': top_products,
            'success_rate': success_rate,
            'failed_rate': failed_rate,
            'recent_orders': recent_orders,
            'confirmed_count': Order.objects.filter(statut='valide').count(),
            'conversion_rate': 3.2,
            'active_section': 'dashboard',
            'months_labels_js': list(months_labels),
            'sales_data_js': list(sales_data),
        })
        return context

class AdminProductListView(AdminRequiredMixin, ListView):
    model = Product
    template_name = 'dashboard/products.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.select_related('cat_id').order_by('-created_at')
        q = self.request.GET.get('q')
        cat_filter = self.request.GET.get('category')
        status = self.request.GET.get('status')
        if q:
            qs = qs.filter(Q(nom_prod__icontains=q) | Q(groupe_id__icontains=q))
        if cat_filter:
            qs = qs.filter(cat_id_id=cat_filter)
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        elif status == 'low_stock':
            qs = qs.filter(variants__stocks__quantity__lte=5).distinct()
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['total_products'] = Product.objects.count()
        context['active_products'] = Product.objects.filter(is_active=True).count()
        context['low_stock_products'] = Product.objects.filter(
            variants__stocks__quantity__lte=5, is_active=True
        ).distinct().count()
        context['active_section'] = 'products'
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        if action == 'toggle_active' and product_id:
            product = get_object_or_404(Product, id=product_id)
            product.is_active = not product.is_active
            product.save()
            messages.success(request, f"Produit '{product.nom_prod}' mis à jour.")
        elif action == 'delete' and product_id:
            product = get_object_or_404(Product, id=product_id)
            product.delete()
            messages.success(request, "Produit supprimé.")
        return redirect('dashboard:products')

class AdminOrderListView(AdminRequiredMixin, ListView):
    model = Order
    template_name = 'dashboard/orders.html'
    context_object_name = 'orders'
    paginate_by = 20

    def get_queryset(self):
        qs = Order.objects.select_related('client_id').order_by('-date_com')
        status = self.request.GET.get('status')
        payment = self.request.GET.get('payment')
        q = self.request.GET.get('q')
        if status:
            qs = qs.filter(statut=status)
        if payment:
            # Payment filtering might need to check Payment table now
            # For simplicity, filter via related 'payments' status
            if payment == 'paid':
                qs = qs.filter(payments__is_valide=True)
            elif payment == 'pending':
                qs = qs.exclude(payments__is_valide=True)
        if q:
            qs = qs.filter(
                Q(order_number__icontains=q) | Q(client_id__username__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUT_CHOICES
        context['payment_choices'] = Order.PAY_MODE_CHOICES
        context['pending_count'] = Order.objects.filter(statut='en_attente').count()
        context['confirmed_count'] = Order.objects.filter(statut='valide').count()
        context['delivered_count'] = Order.objects.filter(statut='livre').count()
        context['active_section'] = 'orders'
        return context

class AdminOrderDetailView(AdminRequiredMixin, DetailView):
    model = Order
    template_name = 'dashboard/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_queryset(self):
        return Order.objects.select_related('client_id').prefetch_related('items__product', 'payments', 'delivery')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUT_CHOICES
        context['livreurs'] = CustomUser.objects.filter(role='livreur', is_dispo=True)
        context['active_section'] = 'orders'
        return context

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        new_status = request.POST.get('status')
        livreur_id = request.POST.get('livreur_id')

        if new_status and new_status in dict(Order.STATUT_CHOICES):
            if order.statut == 'en_attente' and new_status in ['valide', 'expedie', 'livre', 'retrait_valide']:
                from apps.orders.services import OrderService
                OrderService.confirm_payment_and_deduct_stock(order)
            else:
                order.statut = new_status
                order.save()
            messages.success(request, f"Statut de la commande {order.order_number} changé en « {order.get_statut_display()} ».")

            # Retrait validé → paiement automatiquement marqué comme payé
            if new_status == 'retrait_valide':
                from apps.payments.models import Payment
                payment = Payment.objects.filter(com_id=order).first()
                if payment:
                    payment.is_valide = True
                    payment.mt_paye = order.mt_total
                    payment.save()
                else:
                    Payment.objects.create(
                        com_id=order,
                        mode_pay=order.pay_mode if order.pay_mode in ['nelsius', 'fashi', 'cash'] else 'cash',
                        mt_paye=order.mt_total,
                        is_valide=True,
                    )
                messages.success(request, f"Paiement de {order.mt_total} FCFA enregistré automatiquement.")


        if livreur_id:
            livreur = get_object_or_404(CustomUser, id=livreur_id, role='livreur')
            if hasattr(order, 'delivery') and order.delivery is not None:
                # Home delivery: assign livreur and ensure delivery code exists
                order.delivery.livreur_id = livreur
                order.delivery.save()
                if not order.delivery_code:
                    import random
                    order.delivery_code = str(random.randint(100000, 999999))
            # Store pickup: no delivery code is assigned

            # Switch the state to dispatched systematically
            order.statut = 'expedie'
            order.save()

            messages.success(request, f"Commande assignée à {livreur.username}. Le statut est passé à Expédié.")

        return redirect('dashboard:order_detail', order_number=order.order_number)

class AdminUserListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'dashboard/users.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        qs = CustomUser.objects.filter(role='client').order_by('-date_joined')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['total_clients'] = CustomUser.objects.filter(role='client').count()
        context['total_livreurs'] = CustomUser.objects.filter(role='livreur').count()
        context['total_admins'] = CustomUser.objects.filter(role='admin').count()
        context['active_section'] = 'users'
        return context

class AdminStockView(AdminRequiredMixin, TemplateView):
    template_name = 'dashboard/stock.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        threshold = int(self.request.GET.get('threshold', 3))
        # Stocks avec stock faible
        low_stocks = VariantStock.objects.filter(
            quantity__lte=threshold, variant__is_active=True, variant__product__is_active=True
        ).select_related('variant__product', 'store').order_by('variant__product__nom_prod', 'quantity')
        
        # Groupement par produit pour éviter les répétitions
        grouped_stocks = {}
        for vs in low_stocks:
            p = vs.variant.product
            if p.id not in grouped_stocks:
                grouped_stocks[p.id] = {
                    'product': p,
                    'variants': []
                }
            grouped_stocks[p.id]['variants'].append(vs)
            
        context['low_stock_groups'] = grouped_stocks.values()
        context['out_of_stock'] = VariantStock.objects.filter(quantity=0, variant__is_active=True, variant__product__is_active=True).count()
        context['critical'] = VariantStock.objects.filter(quantity__range=(1, 3), variant__is_active=True, variant__product__is_active=True).count()
        context['warning'] = VariantStock.objects.filter(quantity__range=(4, threshold), variant__is_active=True, variant__product__is_active=True).count()
        context['threshold'] = threshold
        context['active_section'] = 'stock'
        return context

    def post(self, request, *args, **kwargs):
        stock_id = request.POST.get('variant_stock_id')
        action = request.POST.get('action')
        new_quantity = request.POST.get('new_stock')

        if stock_id:
            vs = get_object_or_404(VariantStock, id=stock_id)

            if action == 'deactivate':
                variant = vs.variant
                variant.is_active = False
                variant.save(update_fields=['is_active'])
                messages.success(request, f"La variante '{variant.label}' de '{variant.product.nom_prod}' a été désactivée.")
            else:
                if new_quantity is not None and new_quantity != '':
                    vs.quantity = int(new_quantity)
                    vs.save(update_fields=['quantity'])
                    messages.success(request, f"Stock pour {vs.variant.product.nom_prod} ({vs.store.city}) mis à jour : {new_quantity} unités.")

        return redirect(request.path + f"?threshold={request.POST.get('threshold', 5)}")

# --- Gestion des Attributs ---
class AttributeListView(AdminRequiredMixin, View):
    template_name = 'dashboard/attributes.html'

# --- Gestion des Avis ---
class AdminReviewListView(AdminRequiredMixin, ListView):
    model = ProductReview
    template_name = 'dashboard/reviews.html'
    context_object_name = 'reviews'
    paginate_by = 20

    def get_queryset(self):
        qs = ProductReview.objects.select_related('product', 'user').order_by('-created_at')
        status = self.request.GET.get('status')
        if status == 'pending':
            qs = qs.filter(is_approved=False)
        elif status == 'approved':
            qs = qs.filter(is_approved=True)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_section'] = 'reviews'
        context['pending_reviews_count'] = ProductReview.objects.filter(is_approved=False).count()
        return context

class AdminReviewActionView(AdminRequiredMixin, View):
    def post(self, request, pk, action):
        review = get_object_or_404(ProductReview, pk=pk)
        if action == 'approve':
            review.is_approved = True
            review.save()
            messages.success(request, f"L'avis de {review.user.username} a été approuvé.")
        elif action == 'delete':
            review.delete()
            messages.success(request, "L'avis a été supprimé.")
        return redirect('dashboard:reviews')

# --- CRUD Produit ---
class ProductCreateView(AdminRequiredMixin, CreateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:products')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_title'] = "Nouveau Produit"
        context['active_section'] = 'products'
        
        # Préparer les champs par capacité pour le template (évite les filtres custom)
        form = context['form']
        from apps.catalog.models import CAPACITY_CHOICES
        capacity_items = []
        # On itère sur les sous-champs de available_capacities
        # available_capacities est un MultipleChoiceField, ses choix sont des 'BoundWidget'
        for i, (cap_code, cap_label) in enumerate(CAPACITY_CHOICES):
            # On cherche le champ prix correspondant
            price_field = form[f'price_{cap_code}']
            # On cherche le widget checkbox correspondant (index-based)
            # Note: available_capacities.field.choices est la liste des tuples
            capacity_items.append({
                'code': cap_code,
                'label': cap_label,
                'price_field': price_field,
                'checkbox_index': i # On l'utilisera pour identifier la checkbox dans le template
            })
        context['capacity_items'] = capacity_items
        return context

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, "Produit créé avec succès.")
        return redirect(self.success_url)

class ProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:products')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_title'] = f"Modifier {self.object.nom_prod}"
        context['active_section'] = 'products'
        
        # Préparer les champs par capacité pour le template
        form = context['form']
        from apps.catalog.models import CAPACITY_CHOICES
        capacity_items = []
        for i, (cap_code, cap_label) in enumerate(CAPACITY_CHOICES):
            capacity_items.append({
                'code': cap_code,
                'label': cap_label,
                'price_field': form[f'price_{cap_code}'],
                'checkbox_index': i
            })
        context['capacity_items'] = capacity_items
        
        # Add existing variants with their stocks for visualization
        context['existing_variants'] = self.object.variants.all().prefetch_related('stocks__store')
        
        return context

    def form_valid(self, form):
        self.object = form.save()
        messages.success(self.request, "Produit mis à jour.")
        return redirect(self.success_url)

# --- CRUD Catégorie ---
class CategoryListView(AdminRequiredMixin, ListView):
    model = Category
    template_name = 'dashboard/categories.html'
    context_object_name = 'categories'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CategoryForm()
        context['active_section'] = 'products'
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        if action == 'create':
            form = CategoryForm(request.POST, request.FILES)
            if form.is_valid():
                form.save()
                messages.success(request, "Catégorie ajoutée.")
            else:
                messages.error(request, "Erreur lors de l'ajout.")
        elif action == 'delete':
            cat_id = request.POST.get('category_id')
            category = get_object_or_404(Category, id=cat_id)
            if category.products.exists():
                messages.error(request, "Impossible de supprimer une catégorie contenant des produits.")
            else:
                category.delete()
                messages.success(request, "Catégorie supprimée.")
        return redirect('dashboard:categories')

class CategoryUpdateView(AdminRequiredMixin, UpdateView):
    model = Category
    form_class = CategoryForm
    template_name = 'dashboard/category_form.html'
    success_url = reverse_lazy('dashboard:categories')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_title'] = f"Modifier la catégorie : {self.object.nom_cat}"
        context['active_section'] = 'products'
        return context

    def form_valid(self, form):
        messages.success(self.request, "Catégorie mise à jour.")
        return super().form_valid(form)

# --- CRUD Livreur ---
class LivreurListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'dashboard/livreur_list.html'
    context_object_name = 'livreurs'
    paginate_by = 20

    def get_queryset(self):
        qs = CustomUser.objects.filter(role='livreur').annotate(
            commandes_livrees=Count('deliveries__com_id', filter=Q(deliveries__com_id__statut='livre'))
        ).order_by('-date_joined')
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(username__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['active_section'] = 'users'
        context['total_livreurs'] = CustomUser.objects.filter(role='livreur').count()
        return context

class LivreurCreateView(AdminRequiredMixin, CreateView):
    model = CustomUser
    form_class = LivreurCreationForm
    template_name = 'dashboard/livreur_form.html'
    success_url = reverse_lazy('dashboard:livreur_list')

    def form_valid(self, form):
        messages.success(self.request, "Livreur créé avec succès.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_title'] = "Ajouter un Livreur"
        context['active_section'] = 'users'
        return context

class LivreurUpdateView(AdminRequiredMixin, UpdateView):
    model = CustomUser
    form_class = LivreurUpdateForm
    template_name = 'dashboard/livreur_form.html'
    success_url = reverse_lazy('dashboard:livreur_list')

    def get_queryset(self):
        return CustomUser.objects.filter(role='livreur')

    def form_valid(self, form):
        messages.success(self.request, "Informations du livreur mises à jour.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action_title'] = f"Modifier {self.object.username}"
        context['active_section'] = 'users'
        return context

class LivreurDeleteView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        livreur = get_object_or_404(CustomUser, pk=pk, role='livreur')
        if Order.objects.filter(delivery__livreur_id=livreur).exists():  # Quick safety catch
            messages.error(request, f"Impossible de supprimer {livreur.username}.")
        else:
            livreur.delete()
            messages.success(request, f"Livreur {livreur.username} supprimé avec succès.")
        return redirect('dashboard:livreur_list')

class EncaisserSoldeView(AdminRequiredMixin, View):
    def post(self, request, pk, *args, **kwargs):
        livreur = get_object_or_404(CustomUser, pk=pk, role='livreur')
        montant = livreur.solde_coll
        livreur.solde_coll = 0
        livreur.save(update_fields=['solde_coll'])
        messages.success(request, f"Le versement de {livreur.get_full_name() or livreur.username} a été validé avec succès ({montant} FCFA).")
        return redirect('dashboard:livreur_list')


# ── Rapport de Ventes PDF ─────────────────────────────────────────────────────

import io
from datetime import date, timedelta
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa


def _render_to_pdf(template_src, context_dict={}):
    """Génère un PDF à partir d'un template Django."""
    template = get_template(template_src)
    html = template.render(context_dict)
    result = io.BytesIO()
    pdf = pisa.pisaDocument(io.BytesIO(html.encode("UTF-8")), result)
    if not pdf.err:
        return result.getvalue()
    return None


class SalesReportView(AdminRequiredMixin, View):
    """
    Page de sélection de période + génération du rapport PDF de ventes.
    GET  → affiche le formulaire
    POST → valide la période et retourne le PDF en téléchargement
    """
    template_name = 'dashboard/sales_report_filter.html'

    def get(self, request, *args, **kwargs):
        today = date.today()
        default_from = today - timedelta(weeks=2)
        return render(request, self.template_name, {
            'active_section': 'reports',
            'default_from': default_from.strftime('%Y-%m-%d'),
            'default_to': today.strftime('%Y-%m-%d'),
            'today': today.strftime('%Y-%m-%d'),
            'min_date': (today - timedelta(weeks=26)).strftime('%Y-%m-%d'),  # 6 mois max en arrière
        })

    def post(self, request, *args, **kwargs):
        from datetime import datetime

        date_from_str = request.POST.get('date_from')
        date_to_str = request.POST.get('date_to')

        # Validation des dates
        try:
            date_from = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            date_to = datetime.strptime(date_to_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            messages.error(request, "Dates invalides.")
            return redirect('dashboard:sales_report')

        if date_to < date_from:
            messages.error(request, "La date de fin doit être après la date de début.")
            return redirect('dashboard:sales_report')

        delta = (date_to - date_from).days

        if delta < 13:  # moins de 2 semaines (14 jours minimum → 13 jours de différence)
            messages.error(request, "La période doit être d'au moins 2 semaines (14 jours).")
            return redirect('dashboard:sales_report')

        if delta > 183:  # plus de 6 mois (~26 semaines)
            messages.error(request, "La période ne peut pas dépasser 6 mois.")
            return redirect('dashboard:sales_report')

        # ── Collecte des données ──────────────────────────────────────────────
        orders_qs = Order.objects.filter(
            statut__in=['valide', 'livre'],
            date_com__date__gte=date_from,
            date_com__date__lte=date_to,
        ).select_related('client_id').prefetch_related('items__product').order_by('date_com')

        total_revenue = orders_qs.aggregate(total=Sum('mt_total'))['total'] or 0
        total_orders = orders_qs.count()
        delivered_orders = orders_qs.filter(statut='livre').count()
        avg_cart = (total_revenue / total_orders) if total_orders > 0 else 0

        # Top produits sur la période
        top_products = OrderItem.objects.filter(
            order__in=orders_qs
        ).values('product__nom_prod', 'product__marque').annotate(
            qty=Sum('quantity'),
            revenue=Sum('price')
        ).order_by('-revenue')[:10]

        # Découpage par semaine
        weekly_data = []
        current = date_from
        while current <= date_to:
            week_end = min(current + timedelta(days=6), date_to)
            week_orders = orders_qs.filter(date_com__date__gte=current, date_com__date__lte=week_end)
            week_rev = week_orders.aggregate(total=Sum('mt_total'))['total'] or 0
            weekly_data.append({
                'label': f"{current.strftime('%d/%m')} – {week_end.strftime('%d/%m/%Y')}",
                'count': week_orders.count(),
                'revenue': int(week_rev),
            })
            current = week_end + timedelta(days=1)

        context = {
            'date_from': date_from,
            'date_to': date_to,
            'total_revenue': total_revenue,
            'total_orders': total_orders,
            'delivered_orders': delivered_orders,
            'avg_cart': int(avg_cart),
            'orders': orders_qs,
            'top_products': top_products,
            'weekly_data': weekly_data,
            'generated_at': timezone.now(),
        }

        pdf = _render_to_pdf('dashboard/sales_report_pdf.html', context)
        if pdf:
            response = HttpResponse(pdf, content_type='application/pdf')
            filename = f"Rapport_Ventes_{date_from.strftime('%d%m%Y')}_au_{date_to.strftime('%d%m%Y')}.pdf"
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            return response

        messages.error(request, "Erreur lors de la génération du rapport PDF.")
        return redirect('dashboard:sales_report')