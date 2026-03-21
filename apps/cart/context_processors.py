from .services import CartService

def cart(request):
    """
    Rend le panier disponible globalement dans tous les templates
    sous la variable 'cart'.
    """
    # Initialize the cart service with the current request
    # This allows us to use {{ cart|length }} or iterate over {{ cart }} in any template
    return {'cart': CartService(request)}
