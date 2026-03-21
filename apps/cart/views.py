from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from apps.catalog.models import Product
from .services import CartService

# Duplicate cart_detail removed
@require_POST
def cart_add_ajax(request, product_id):
    """Endpoint AJAX — retourne du JSON, sans rechargement de page."""
    cart = CartService(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override', False) == 'True'
    
    color = request.POST.get('color')
    capacity = request.POST.get('capacity')
    variant_id = request.POST.get('variant_id')

    # Si on a un variant_id, on peut l'utiliser pour récupérer les infos précises
    if variant_id:
        from apps.catalog.models import ProductVariant
        try:
            variant = ProductVariant.objects.get(id=variant_id)
            color = variant.color.name if variant.color else color
            capacity = variant.capacity.value if variant.capacity else capacity
        except ProductVariant.DoesNotExist:
            pass

    if product.stock >= quantity or (variant_id and variant.stock >= quantity):
        cart.add(product=product, quantity=quantity, override_quantity=override, color=color, capacity=capacity)
        count = len(cart)
        return JsonResponse({
            'success': True,
            'count': count,
            'message': f'"{product.name}" ajouté au panier',
        })
    else:
        return JsonResponse({
            'success': False,
            'count': len(cart),
            'message': 'Stock insuffisant pour ce produit.',
        }, status=400)

def cart_detail(request):
    cart = CartService(request)
    recent_products = Product.objects.filter(is_active=True).order_by('-created_at')[:4]
    return render(request, 'cart/detail.html', {'cart': cart, 'recent_products': recent_products})

@require_POST
def cart_add(request, product_id):
    cart = CartService(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override', False) == 'True'
    
    color = request.POST.get('color')
    capacity = request.POST.get('capacity')
    variant_id = request.POST.get('variant_id')

    if variant_id:
        from apps.catalog.models import ProductVariant
        try:
            variant = ProductVariant.objects.get(id=variant_id)
            color = variant.color.name if variant.color else color
            capacity = variant.capacity.value if variant.capacity else capacity
        except ProductVariant.DoesNotExist:
            pass

    if product.stock >= quantity or (variant_id and variant.stock >= quantity):
        cart.add(product=product, quantity=quantity, override_quantity=override, color=color, capacity=capacity)
    
    # Redirige vers la page d'origine, pas le panier
    next_url = request.POST.get('next') or request.META.get('HTTP_REFERER', '')
    if next_url:
        return redirect(next_url)
    return redirect('cart:cart_detail')

@require_POST
def cart_remove(request, product_id):
    cart = CartService(request)
    product = get_object_or_404(Product, id=product_id)
    cart.remove(product)
    return redirect('cart:cart_detail')

def cart_clear(request):
    cart = CartService(request)
    cart.clear()
    return redirect('cart:cart_detail')
