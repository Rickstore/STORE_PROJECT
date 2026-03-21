from django.views.generic import TemplateView, ListView, DetailView, View, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.contrib import messages
from django.shortcuts import redirect, get_object_or_404
from django.http import JsonResponse
from apps.orders.models import Order, OrderItem
from apps.catalog.models import Product, Category, ProductReview, ProductSpecification, Color, Capacity
from apps.users.models import CustomUser
from .forms import ProductForm, CategoryForm, LivreurCreationForm, LivreurUpdateForm, ProductSpecificationFormSet, ProductVariantFormSet, ColorForm, CapacityForm
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

        total_revenue = Order.objects.filter(status='delivered').aggregate(
            total=Sum('total'))['total'] or 0
        total_orders = Order.objects.count()
        orders_today = Order.objects.filter(created_at__date=today).count()
        
        success_deliveries = Order.objects.filter(status='delivered').count()
        avg_cart = (total_revenue / success_deliveries) if success_deliveries > 0 else 0
        low_stock_count = Product.objects.filter(stock__lte=5, is_active=True).count()
        pending_orders = Order.objects.filter(status='pending').count()
        pending_reviews = ProductReview.objects.filter(is_approved=False).count()

        top_products = OrderItem.objects.filter(
            order__status='delivered'
        ).values('product__brand', 'product__name').annotate(
            total_sales_value=Sum('price'),
            total_sold=Sum('quantity')
        ).order_by('-total_sales_value')[:4]

        total_deliveries = Order.objects.exclude(status='pending').count()
        success_deliveries = Order.objects.filter(status='delivered').count()
        failed_deliveries = Order.objects.filter(status='failed').count()
        success_rate = (success_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0
        failed_rate = (failed_deliveries / total_deliveries * 100) if total_deliveries > 0 else 0

        recent_orders = Order.objects.select_related('user').order_by('-created_at')[:6]

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
            'conversion_rate': 3.2,
            'active_section': 'dashboard',
        })
        return context


class AdminProductListView(AdminRequiredMixin, ListView):
    model = Product
    template_name = 'dashboard/products.html'
    context_object_name = 'products'
    paginate_by = 20

    def get_queryset(self):
        qs = Product.objects.select_related('category').order_by('-created_at')
        q = self.request.GET.get('q')
        brand = self.request.GET.get('brand')
        status = self.request.GET.get('status')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(brand__icontains=q))
        if brand:
            qs = qs.filter(brand=brand)
        if status == 'active':
            qs = qs.filter(is_active=True)
        elif status == 'inactive':
            qs = qs.filter(is_active=False)
        elif status == 'low_stock':
            qs = qs.filter(stock__lte=5)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['brands'] = Product.objects.values_list('brand', flat=True).distinct().order_by('brand')
        context['categories'] = Category.objects.all()
        context['total_products'] = Product.objects.count()
        context['active_products'] = Product.objects.filter(is_active=True).count()
        context['low_stock_products'] = Product.objects.filter(stock__lte=5, is_active=True).count()
        context['active_section'] = 'products'
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        product_id = request.POST.get('product_id')
        if action == 'toggle_active' and product_id:
            product = get_object_or_404(Product, id=product_id)
            product.is_active = not product.is_active
            product.save()
            messages.success(request, f"Produit '{product.name}' mis à jour.")
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
        qs = Order.objects.select_related('user', 'address').order_by('-created_at')
        status = self.request.GET.get('status')
        payment = self.request.GET.get('payment')
        q = self.request.GET.get('q')
        if status:
            qs = qs.filter(status=status)
        if payment:
            qs = qs.filter(payment_status=payment)
        if q:
            qs = qs.filter(
                Q(order_number__icontains=q) | Q(user__username__icontains=q)
            )
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        context['payment_choices'] = Order.PAYMENT_STATUS_CHOICES
        context['pending_count'] = Order.objects.filter(status='pending').count()
        context['confirmed_count'] = Order.objects.filter(status='confirmed').count()
        context['delivered_count'] = Order.objects.filter(status='delivered').count()
        context['active_section'] = 'orders'
        return context


class AdminOrderDetailView(AdminRequiredMixin, DetailView):
    model = Order
    template_name = 'dashboard/order_detail.html'
    context_object_name = 'order'
    slug_field = 'order_number'
    slug_url_kwarg = 'order_number'

    def get_queryset(self):
        return Order.objects.select_related('user', 'address', 'store', 'assigned_delivery').prefetch_related('items__product')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['status_choices'] = Order.STATUS_CHOICES
        context['livreurs'] = CustomUser.objects.filter(role='livreur')
        context['active_section'] = 'orders'
        return context

    def post(self, request, *args, **kwargs):
        order = self.get_object()
        new_status = request.POST.get('status')
        livreur_id = request.POST.get('livreur_id')

        if new_status and new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            messages.success(request, f"Statut de la commande {order.order_number} changé en « {order.get_status_display()} ».")

        if livreur_id:
            livreur = get_object_or_404(CustomUser, id=livreur_id, role='livreur')
            order.assigned_delivery = livreur
            order.save()
            messages.success(request, f"Commande assignée à {livreur.username}.")

        return redirect('dashboard:order_detail', order_number=order.order_number)


class AdminUserListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'dashboard/users.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        # L'admin ne voit que les clients
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
        threshold = int(self.request.GET.get('threshold', 5))
        context['low_stock_products'] = Product.objects.filter(
            stock__lte=threshold, is_active=True
        ).select_related('category').order_by('stock')
        context['out_of_stock'] = Product.objects.filter(stock=0, is_active=True).count()
        context['critical'] = Product.objects.filter(stock__gte=1, stock__lte=3, is_active=True).count()
        context['warning'] = Product.objects.filter(stock__gte=4, stock__lte=threshold, is_active=True).count()
        context['threshold'] = threshold
        context['active_section'] = 'stock'
        return context

    def post(self, request, *args, **kwargs):
        product_id = request.POST.get('product_id')
        new_stock = request.POST.get('stock')
        if product_id and new_stock is not None:
            product = get_object_or_404(Product, id=product_id)
            product.stock = int(new_stock)
            product.save()
            messages.success(request, f"Stock de « {product.name} » mis à jour : {product.stock} unités.")
        return redirect(request.path + f"?threshold={request.POST.get('threshold', 5)}")


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
        if self.request.POST:
            context['specifications'] = ProductSpecificationFormSet(self.request.POST)
            context['variants'] = ProductVariantFormSet(self.request.POST)
        else:
            context['specifications'] = ProductSpecificationFormSet()
            context['variants'] = ProductVariantFormSet()
        context['action_title'] = "Nouveau Produit"
        context['active_section'] = 'products'
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        specifications = context['specifications']
        variants = context['variants']
        if specifications.is_valid() and variants.is_valid():
            self.object = form.save()
            specifications.instance = self.object
            specifications.save()
            variants.instance = self.object
            variants.save()
            messages.success(self.request, "Produit créé avec succès.")
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form, specifications=specifications, variants=variants))

class ProductUpdateView(AdminRequiredMixin, UpdateView):
    model = Product
    form_class = ProductForm
    template_name = 'dashboard/product_form.html'
    success_url = reverse_lazy('dashboard:products')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['specifications'] = ProductSpecificationFormSet(self.request.POST, instance=self.object)
            context['variants'] = ProductVariantFormSet(self.request.POST, instance=self.object)
        else:
            context['specifications'] = ProductSpecificationFormSet(instance=self.object)
            context['variants'] = ProductVariantFormSet(instance=self.object)
        context['action_title'] = f"Modifier {self.object.name}"
        context['active_section'] = 'products'
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        specifications = context['specifications']
        variants = context['variants']
        if specifications.is_valid() and variants.is_valid():
            self.object = form.save()
            specifications.instance = self.object
            specifications.save()
            variants.instance = self.object
            variants.save()
            messages.success(self.request, "Produit mis à jour.")
            return redirect(self.success_url)
        else:
            return self.render_to_response(self.get_context_data(form=form, specifications=specifications, variants=variants))

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
        context['action_title'] = f"Modifier la catégorie : {self.object.name}"
        context['active_section'] = 'products'
        return context

    def form_valid(self, form):
        messages.success(self.request, "Catégorie mise à jour.")
        return super().form_valid(form)

class AttributeManagementView(AdminRequiredMixin, TemplateView):
    template_name = 'dashboard/attributes.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['colors'] = Color.objects.all()
        context['capacities'] = Capacity.objects.all()
        context['color_form'] = ColorForm()
        context['capacity_form'] = CapacityForm()
        context['active_section'] = 'products'
        return context

    def post(self, request, *args, **kwargs):
        action = request.POST.get('action')
        if action == 'add_color':
            form = ColorForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Couleur ajoutée.")
            else:
                messages.error(request, "Erreur lors de l'ajout de la couleur.")
        elif action == 'delete_color':
            color_id = request.POST.get('color_id')
            color = get_object_or_404(Color, id=color_id)
            color.delete()
            messages.success(request, "Couleur supprimée.")
        elif action == 'add_capacity':
            form = CapacityForm(request.POST)
            if form.is_valid():
                form.save()
                messages.success(request, "Capacité ajoutée.")
            else:
                messages.error(request, "Erreur lors de l'ajout de la capacité.")
        elif action == 'delete_capacity':
            cap_id = request.POST.get('capacity_id')
            capacity = get_object_or_404(Capacity, id=cap_id)
            capacity.delete()
            messages.success(request, "Capacité supprimée.")
        return redirect('dashboard:attributes')

        return redirect('dashboard:attributes')

# --- CRUD Livreur ---

class LivreurListView(AdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'dashboard/livreur_list.html'
    context_object_name = 'livreurs'
    paginate_by = 20

    def get_queryset(self):
        qs = CustomUser.objects.filter(role='livreur').order_by('-date_joined')
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
        if Order.objects.filter(assigned_delivery=livreur, status__in=['confirmed', 'shipped']).exists():
            messages.error(request, f"Impossible de supprimer {livreur.username} car il gère des commandes en cours.")
        else:
            livreur.delete()
            messages.success(request, f"Livreur {livreur.username} supprimé avec succès.")
        return redirect('dashboard:livreur_list')

