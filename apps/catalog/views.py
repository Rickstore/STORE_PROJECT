import json
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Product, ProductVariant, Category, ProductReview, Store, COLOR_CODES
from django.contrib.auth.mixins import UserPassesTestMixin


class LivreurRestrictionMixin(UserPassesTestMixin):
    """Vérifie que l'utilisateur n'est pas un livreur avant d'accéder au catalogue."""
    def test_func(self):
        if self.request.user.is_authenticated:
            return self.request.user.role != 'livreur'
        return True

    def handle_no_permission(self):
        if self.request.user.is_authenticated and self.request.user.role == 'livreur':
            return redirect('delivery:dashboard')
        return redirect('users:login')


class HomeView(LivreurRestrictionMixin, TemplateView):
    """Vue pour la page d'accueil avec les produits mis en avant et les catégories."""
    template_name = 'catalog/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Product.objects.filter(
            is_active=True
        ).exclude(
            Q(is_2ndmain=True) | Q(fast_deal=True)
        ).prefetch_related('images', 'variants').order_by('-created_at')[:8]
        context['categories'] = Category.objects.all()
        context['fast_deal_products'] = Product.objects.filter(
            Q(is_2ndmain=True) | Q(fast_deal=True),
            is_active=True
        ).prefetch_related('images', 'variants').order_by('-created_at')[:6]
        return context


class CatalogView(LivreurRestrictionMixin, ListView):
    """Vue pour le catalogue avec filtrage par catégorie, recherche et prix."""
    model = Product
    template_name = 'catalog/catalog.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_template_names(self):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return ['catalog/product_list_partial.html']
        return [self.template_name]

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).prefetch_related('images', 'variants').order_by('-created_at')
        category_slug = self.request.GET.get('category')
        search_query = self.request.GET.get('q')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if category_slug:
            queryset = queryset.filter(cat_id__slug_cat=category_slug)
        if search_query:
            queryset = queryset.filter(
                Q(nom_prod__icontains=search_query) |
                Q(specs__icontains=search_query) |
                Q(description__icontains=search_query)
            )
        # Filtrage par prix via les variantes
        if min_price and min_price.isdigit():
            queryset = queryset.filter(variants__prix_unit__gte=min_price)
        if max_price and max_price.isdigit():
            queryset = queryset.filter(variants__prix_unit__lte=max_price)

        state = self.request.GET.get('state')
        if state == 'second_hand':
            queryset = queryset.filter(is_2ndmain=True)

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        category_slug = self.request.GET.get('category')
        if category_slug:
            context['active_category'] = Category.objects.filter(slug_cat=category_slug).first()
        context['brands'] = []
        context['current_category'] = category_slug or ''
        context['search_query'] = self.request.GET.get('q', '')
        context['current_min_price'] = self.request.GET.get('min_price', '')
        context['current_max_price'] = self.request.GET.get('max_price', '')
        context['current_state'] = self.request.GET.get('state', '')
        return context


class ProductDetailView(LivreurRestrictionMixin, DetailView):
    """Vue détaillée d'un produit avec gestion des variantes, avis et produits similaires."""
    model = Product
    template_name = 'catalog/detail.html'
    context_object_name = 'product'

    def get_template_names(self):
        if self.request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return ['catalog/product_detail_partial.html']
        return [self.template_name]

    def get_queryset(self):
        return Product.objects.filter(is_active=True).prefetch_related('images', 'variants__stocks__store', 'reviews')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object

        # ----------------------------------------------------------------
        # Variantes actives
        # ----------------------------------------------------------------
        variants = product.variants.filter(is_active=True)

        # Couleurs et capacités disponibles
        colors_set = sorted({v.couleur for v in variants if v.couleur})
        capacities_set = sorted({v.capacite for v in variants if v.capacite})

        context['available_colors'] = colors_set
        context['available_capacities'] = capacities_set
        context['color_codes'] = COLOR_CODES
        context['color_variants'] = [
            {'name': c, 'code': COLOR_CODES.get(c, '#CCCCCC')}
            for c in colors_set
        ]

        # ----------------------------------------------------------------
        # Sérialisation JSON des variantes pour le JS dynamique
        # Format: { "Noir_128Go": {variant_id, price, stocks: {store_id: qty}, in_stock: total>0, image_url}, ... }
        # ----------------------------------------------------------------
        variants_map = {}
        for v in variants:
            key = f"{v.couleur or ''}_{v.capacite or ''}"
            
            # Construire le dictionnaire de stocks par boutique
            store_stocks = {}
            for vs in v.stocks.all():
                store_stocks[vs.store.id] = vs.quantity

            variants_map[key] = {
                'variant_id': v.id,
                'price': int(v.prix_unit),
                'stock_total': v.stock,
                'stocks': store_stocks,
                'in_stock': v.is_in_stock,
                'image_url': v.image.url if v.image else None,
                'color': v.couleur,
                'capacity': v.capacite,
                'label': v.label,
            }
        context['variants_json'] = json.dumps(variants_map, ensure_ascii=False)
        context['stores'] = Store.objects.all()
        context['stores_json'] = json.dumps([
            {'id': s.id, 'name': s.name, 'city': s.city} for s in context['stores']
        ], ensure_ascii=False)

        # ----------------------------------------------------------------
        # Produits similaires (même catégorie, produit différent)
        # ----------------------------------------------------------------
        related = Product.objects.filter(
            cat_id=product.cat_id,
            is_active=True
        ).exclude(pk=product.pk).prefetch_related('images', 'variants')[:4]
        context['related_products'] = related

        # Ancienne compat: group_variants (produits similaires même groupe)
        context['group_variants'] = []

        # ----------------------------------------------------------------
        # Avis clients approuvés
        # ----------------------------------------------------------------
        context['reviews'] = product.reviews.filter(is_approved=True).select_related('user').order_by('-created_at')
        context['user_has_reviewed'] = (
            self.request.user.is_authenticated and
            product.reviews.filter(user=self.request.user).exists()
        )
        return context

    def post(self, request, *args, **kwargs):
        """Traiter la soumission d'un nouvel avis client."""
        product = self.get_object()
        if not request.user.is_authenticated:
            messages.error(request, "Vous devez être connecté pour laisser un avis.")
            return redirect('users:login')

        if product.reviews.filter(user=request.user).exists():
            messages.warning(request, "Vous avez déjà laissé un avis sur ce produit.")
        else:
            rating = request.POST.get('rating')
            comment = request.POST.get('comment', '').strip()
            if rating:
                ProductReview.objects.create(
                    product=product,
                    user=request.user,
                    rating=int(rating),
                    comment=comment,
                )
                messages.success(request, "Votre avis a été soumis et est en attente de validation.")
            else:
                messages.error(request, "Veuillez choisir une note.")
        return redirect('catalog:product_detail', pk=product.id)


# ---------------------------------------------------------------------------
# API JSON — données d'une variante
# ---------------------------------------------------------------------------

def variant_data(request, pk):
    """Retourne les données d'une variante en JSON (utilisé par le JS client)."""
    variant = get_object_or_404(ProductVariant.objects.prefetch_related('stocks__store'), pk=pk, is_active=True)

    store_stocks = {}
    for vs in variant.stocks.all():
        store_stocks[vs.store.id] = vs.quantity

    data = {
        'variant_id': variant.id,
        'price': int(variant.prix_unit),
        'stock_total': variant.stock,
        'stocks': store_stocks,
        'in_stock': variant.is_in_stock,
        'color': variant.couleur,
        'capacity': variant.capacite,
        'label': variant.label,
        'image_url': variant.image.url if variant.image else None,
        'color_code': variant.color_code,
    }
    return JsonResponse(data)


class GarantieView(TemplateView):
    """Page de politique de garantie et retour."""
    template_name = 'catalog/garantie.html'
