from decimal import Decimal
from django.conf import settings
from apps.catalog.models import Product

class CartService:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, product, quantity=1, override_quantity=False, color=None, capacity=None):
        product_id = str(product.id)
        # Créer une clé unique basée sur le produit et ses attributs
        item_key = f"{product_id}_{color or ''}_{capacity or ''}"
        
        if item_key not in self.cart:
            self.cart[item_key] = {
                'product_id': product_id,
                'quantity': 0, 
                'price': str(product.price),
                'color': color,
                'capacity': capacity
            }
        
        if override_quantity:
            self.cart[item_key]['quantity'] = quantity
        else:
            self.cart[item_key]['quantity'] += quantity
            
        self.save()

    def remove(self, product, color=None, capacity=None):
        item_key = f"{product.id}_{color or ''}_{capacity or ''}"
        if item_key in self.cart:
            del self.cart[item_key]
            self.save()

    def __iter__(self):
        # Extraire les IDs de produits uniques depuis les valeurs du panier
        product_ids = {item['product_id'] for item in self.cart.values()}
        products = Product.objects.in_bulk(product_ids)
        
        cart = self.cart.copy()
        for item_key, item in cart.items():
            product_id = int(item['product_id'])
            item['product'] = products.get(product_id)
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            item['key'] = item_key
            yield item

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())
        
    def clear(self):
        if settings.CART_SESSION_ID in self.session:
            del self.session[settings.CART_SESSION_ID]
            self.save()

    def save(self):
        self.session.modified = True
