from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.urls import reverse

class Store(models.Model):
    name = models.CharField(max_length=100, verbose_name="Nom du magasin")
    city = models.CharField(max_length=100, verbose_name="Ville")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")
    
    class Meta:
        verbose_name = "Magasin"
        verbose_name_plural = "Magasins"
        
    def __str__(self):
        return f"{self.name} - {self.city}"


class Category(models.Model):
    CATEGORY_ICONS = {
        'smartphone': 'fa-mobile-screen',
        'tablette': 'fa-tablet-screen-button',
        'montre': 'fa-clock',
        'pochette': 'fa-bag-shopping',
        'ecouteur': 'fa-headphones',
    }

    name = models.CharField(max_length=100, verbose_name="Nom")
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Description")
    image = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Image")
    
    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
        
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Garantir l'unicité du slug
            unique_slug = self.slug
            num = 1
            while Category.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{self.slug}-{num}'
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)
        
    def __str__(self):
        return self.name

    @property
    def icon(self):
        for key, icon in self.CATEGORY_ICONS.items():
            if key in self.slug:
                return icon
        return 'fa-tag'

class Color(models.Model):
    name = models.CharField(max_length=50, verbose_name="Nom (ex: Titane)")
    code = models.CharField(max_length=7, help_text="Code Hexa (ex: #C0C0C0)")

    def __str__(self):
        return self.name

class Capacity(models.Model):
    value = models.CharField(max_length=20, verbose_name="Valeur (ex: 128 GB)")

    def __str__(self):
        return self.value
    
class Warehouse(models.Model):
    name = models.CharField(max_length=100)  # ex : Douala - Akwa
    def __str__(self): return self.name

class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nom du produit")
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(verbose_name="Description", blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Prix (FCFA)")
    capacity = models.PositiveIntegerField(default=0, blank=True, verbose_name="Capacité (Go)")
   
    # La marque est désormais un simple champ texte — pas de table séparée
    brand = models.CharField(max_length=100, verbose_name="Marque", default="")
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name="products", verbose_name="Catégorie")
    stock = models.PositiveIntegerField(default=0, verbose_name="Stock disponible")
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Image")
    available_colors = models.ManyToManyField(Color, blank=True)
    available_capacities = models.ManyToManyField(Capacity, blank=True)
    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_second_hand = models.BooleanField(default=False, verbose_name="Seconde main")
    fast_deal = models.BooleanField(default=False, verbose_name="Fast Deal (offre rapide)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    
    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-created_at']
        
    def save(self, *args, **kwargs):
        if not self.slug:
            # Utiliser la marque et le nom pour un slug plus descriptif
            base_slug = slugify(f"{self.brand} {self.name}")
            self.slug = base_slug
            # Garantir l'unicité du slug
            unique_slug = self.slug
            num = 1
            while Product.objects.filter(slug=unique_slug).exists():
                unique_slug = f'{base_slug}-{num}'
                num += 1
            self.slug = unique_slug
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.brand} {self.name}"
        
    @property
    def is_in_stock(self):
        if self.variants.exists():
            return any(v.stock > 0 for v in self.variants.all())
        return self.stock > 0

    @property
    def avg_rating(self):
        reviews = self.reviews.all()
        if reviews.exists():
            return round(sum(r.rating for r in reviews) / reviews.count(), 1)
        return None

    @property
    def get_absolute_url(self):
        return reverse('catalog:product_detail', args=[self.slug])


class ProductSpecification(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='specifications')
    name = models.CharField(max_length=100, verbose_name="Nom de la caractéristique (ex: Écran, Batterie)")
    value = models.CharField(max_length=255, verbose_name="Valeur (ex: 6.1 pouces, 3000 mAh)")

    class Meta:
        verbose_name = "Caractéristique Technique"
        verbose_name_plural = "Caractéristiques Techniques"
        ordering = ['id']

    def __str__(self):
        return f"{self.name}: {self.value}"


class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='products/', blank=True, null=True, verbose_name="Image")
    color = models.ForeignKey(Color, on_delete=models.CASCADE, null=True, blank=True)
    capacity = models.ForeignKey(Capacity, on_delete=models.CASCADE, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name="Prix (FCFA)")
    stock = models.PositiveIntegerField(default=0)

    def __str__(self):
        color_str = self.color.name if self.color else "N/A"
        capacity_str = self.capacity.value if self.capacity else "N/A"
        return f"{self.product.name} - {color_str} - {capacity_str}"


class ProductReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews', verbose_name="Produit")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reviews', verbose_name="Client")
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES, verbose_name="Note")
    comment = models.TextField(verbose_name="Commentaire", blank=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date")
    is_approved = models.BooleanField(default=False, verbose_name="Approuvé")

    class Meta:
        verbose_name = "Avis"
        verbose_name_plural = "Avis"
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # Un seul avis par produit et par utilisateur

    def __str__(self):
        return f"Avis de {self.user.username} sur {self.product.name}"
    

class Stock(models.Model):
    variant = models.ForeignKey(ProductVariant, related_name='stocks', on_delete=models.CASCADE)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=0)
