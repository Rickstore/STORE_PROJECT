from decimal import Decimal
from django.conf import settings
from apps.catalog.models import Product, ProductVariant, Store


class CartService:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart: dict = cart

    def add(self, product, quantity=1, override_quantity=False, color=None, capacity=None, variant=None, store=None):
        """Ajoute un produit (avec sa variante et sa boutique optionnelles) au panier."""
        product_id = str(product.id)
        variant_id = str(variant.id) if variant else ''
        store_id = str(store.id) if store else ''

        # Clé unique = produit + variante + boutique
        item_key = f"{product_id}_{variant_id or f'{color or ''}_{capacity or ''}'}_{store_id}"

        # Prix = celui de la variante si disponible, sinon prix produit
        if variant:
            current_price = str(variant.prix_unit)
        else:
            current_price = str(product.default_price or 0)

        if item_key not in self.cart:
            self.cart[item_key] = {
                'product_id': product_id,
                'variant_id': variant_id,
                'store_id': store_id,
                'quantity': 0,
                'price': current_price,
                'color': color or (variant.couleur if variant else None),
                'capacity': capacity or (variant.capacite if variant else None),
            }

        if override_quantity:
            self.cart[item_key]['quantity'] = quantity
        else:
            self.cart[item_key]['quantity'] += quantity

        self.save()

    def remove(self, item_key):
        """Supprime un article en utilisant sa clé unique."""
        if item_key in self.cart:
            del self.cart[item_key]
            self.save()

    def update_quantity(self, item_key, quantity):
        """Met à jour la quantité d'un article spécifique via sa clé."""
        if item_key in self.cart:
            if int(quantity) > 0:
                self.cart[item_key]['quantity'] = int(quantity)
            else:
                del self.cart[item_key]
            self.save()

    def __iter__(self):
        product_ids = {item['product_id'] for item in self.cart.values()}
        products = Product.objects.in_bulk(product_ids)

        # Charger les variantes en un seul appel
        variant_ids = {item['variant_id'] for item in self.cart.values() if item.get('variant_id')}
        variants = ProductVariant.objects.in_bulk(variant_ids) if variant_ids else {}

        # Charger les boutiques en un seul appel
        store_ids = {item['store_id'] for item in self.cart.values() if item.get('store_id')}
        stores = Store.objects.in_bulk(store_ids) if store_ids else {}

        cart = self.cart.copy()
        for item_key, item_data in cart.items():
            item = item_data.copy()
            product_id = int(item['product_id'])
            item['product'] = products.get(product_id)

            variant_id = item.get('variant_id')
            if variant_id:
                item['variant'] = variants.get(int(variant_id))
            else:
                item['variant'] = None

            store_id = item.get('store_id')
            if store_id:
                item['store'] = stores.get(int(store_id))
            else:
                item['store'] = None

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
