from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_POST
from django.http import JsonResponse
from apps.catalog.models import Product, ProductVariant, Store
from .services import CartService
from django.contrib import messages


def cart_detail(request):
    cart = CartService(request)
    recent_products = Product.objects.filter(is_active=True).prefetch_related('images', 'variants').order_by('-created_at')[:4]
    return render(request, 'cart/detail.html', {'cart': cart, 'recent_products': recent_products})


@require_POST
def cart_add(request, product_id):
    cart = CartService(request)
    product = get_object_or_404(Product, id=product_id)
    quantity = int(request.POST.get('quantity', 1))
    override = request.POST.get('override', False) == 'True'

    # Récupération de la variante
    variant_id = request.POST.get('variant_id')
    variant = None
    if variant_id:
        try:
            variant = ProductVariant.objects.get(id=variant_id, product=product, is_active=True)
        except ProductVariant.DoesNotExist:
            error_msg = "Variante introuvable ou indisponible."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': error_msg}, status=400)
            messages.error(request, error_msg)
            return redirect(request.META.get('HTTP_REFERER', 'catalog:catalog'))

    store_id = request.POST.get('store_id')
    store = None
    if store_id:
        store = Store.objects.filter(id=store_id).first()

    # Vérification du stock
    if variant and store:
        vs = variant.stocks.filter(store=store).first()
        available_stock = vs.quantity if vs else 0
    elif variant:
        available_stock = variant.stock
    else:
        available_stock = product.stock_total

    if available_stock >= quantity:
        cart.add(
            product=product,
            quantity=quantity,
            override_quantity=override,
            color=request.POST.get('color'),
            capacity=request.POST.get('capacity'),
            variant=variant,
            store=store,
        )

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'count': len(cart),
                'total_items': len(cart),
                'message': f'"{product.nom_prod}" ajouté au panier',
            })

        messages.success(request, f'"{product.nom_prod}" ajouté au panier')
        return redirect('cart:cart_detail')
    else:
        error_msg = "Stock insuffisant pour ce produit."
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': error_msg}, status=400)
        messages.error(request, error_msg)
        return redirect(request.META.get('HTTP_REFERER', 'cart:cart_detail'))


@require_POST
def cart_remove(request, item_key):
    """Supprime un article du panier via sa clé unique."""
    cart = CartService(request)
    cart.remove(item_key)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'count': len(cart),
            'total_price': cart.get_total_price(),
            'message': 'Produit retiré du panier'
        })
    return redirect('cart:cart_detail')


@require_POST
def cart_update_ajax(request, item_key):
    """Mise à jour de la quantité via AJAX uniquement."""
    cart = CartService(request)
    quantity = int(request.POST.get('quantity', 1))

    cart.update_quantity(item_key, quantity)

    item = cart.cart.get(item_key)
    if not item:
        return JsonResponse({'success': True, 'count': len(cart), 'removed': True})

    return JsonResponse({
        'success': True,
        'count': len(cart),
        'total_price': cart.get_total_price(),
        'item_total': float(item['price']) * item['quantity'],
        'message': 'Quantité mise à jour'
    })


def cart_clear(request):
    cart = CartService(request)
    cart.clear()
    return redirect('cart:cart_detail')
