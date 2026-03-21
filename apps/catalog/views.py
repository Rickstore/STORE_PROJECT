from django.shortcuts import render, get_object_or_404, redirect

from django.views.generic import ListView, DetailView, TemplateView
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Product, Category, ProductReview


class HomeView(TemplateView):
    template_name = 'catalog/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_products'] = Product.objects.filter(is_active=True).order_by('-created_at')[:8]
        context['categories'] = Category.objects.all()
        context['fast_deal_products'] = Product.objects.filter(
            is_active=True, is_second_hand=True, fast_deal=True
        ).order_by('-created_at')[:6]
        return context


class CatalogView(ListView):
    model = Product
    template_name = 'catalog/catalog.html'
    context_object_name = 'products'
    paginate_by = 12

    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True).order_by('-created_at')
        category_slug = self.request.GET.get('category')
        search_query = self.request.GET.get('q')
        brand_filter = self.request.GET.get('brand')
        min_price = self.request.GET.get('min_price')
        max_price = self.request.GET.get('max_price')

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(brand__icontains=search_query)
            )
        if brand_filter:
            queryset = queryset.filter(brand__icontains=brand_filter)
        if min_price and min_price.isdigit():
            queryset = queryset.filter(price__gte=min_price)
        if max_price and max_price.isdigit():
            queryset = queryset.filter(price__lte=max_price)
            
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        # Valeurs de marques distinctes extraites des produits
        context['brands'] = Product.objects.filter(is_active=True).values_list('brand', flat=True).distinct().order_by('brand')
        context['current_category'] = self.request.GET.get('category', '')
        context['current_brand'] = self.request.GET.get('brand', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['current_min_price'] = self.request.GET.get('min_price', '')
        context['current_max_price'] = self.request.GET.get('max_price', '')
        return context


class ProductDetailView(DetailView):
    model = Product
    template_name = 'catalog/detail.html'
    context_object_name = 'product'
    products = Product.objects.all().prefetch_related('variants')

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        # Produits similaires : même catégorie, produit différent
        related = Product.objects.filter(
            category=product.category, 
            is_active=True
        ).exclude(id=product.id)
        
        # Si pas assez dans la catégorie, compléter avec la même marque
        if related.count() < 3:
            brand_related = Product.objects.filter(
                brand=product.brand,
                is_active=True
            ).exclude(id__in=[product.id] + [p.id for p in related])
            related = list(related) + list(brand_related[:3-len(related)])
        else:
            related = related[:3]

        context['related_products'] = related
        context['reviews'] = product.reviews.filter(is_approved=True).select_related('user').order_by('-created_at')
        context['user_has_reviewed'] = (
            self.request.user.is_authenticated and
            product.reviews.filter(user=self.request.user).exists()
        )
        return context

    def post(self, request, *args, **kwargs):
        """Traiter la soumission d'un avis client."""
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
        return redirect('catalog:product_detail', slug=product.slug)

