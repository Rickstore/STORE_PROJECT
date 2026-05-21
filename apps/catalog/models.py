from django.db import models
from django.utils.text import slugify
from django.conf import settings
from django.urls import reverse


class Store(models.Model):
    #Modèle représentant un point de vente physique.
    name = models.CharField(max_length=100, verbose_name="Nom du magasin")
    city = models.CharField(max_length=100, verbose_name="Ville")
    address = models.TextField(blank=True, null=True, verbose_name="Adresse")

    class Meta:
        verbose_name = "Magasin"
        verbose_name_plural = "Magasins"

    def __str__(self):
        return f"{self.name} - {self.city}"

class Category(models.Model):
    #Modèle pour les catégories de produits avec icônes dynamiques.
    CATEGORY_ICONS = {
        'smartphone': 'fa-mobile-screen',
        'tablette': 'fa-tablet-screen-button',
        'montre': 'fa-clock',
        'pochette': 'fa-bag-shopping',
        'ecouteur': 'fa-headphones',
    }

    nom_cat = models.CharField(max_length=100, verbose_name="Nom", help_text="Nom de la catégorie", default='')
    slug_cat = models.SlugField(unique=True, blank=True, help_text="Identifiant unique")
    desc_cat = models.TextField(blank=True, verbose_name="Description", help_text="Description de la catégorie")
    img_cat = models.ImageField(upload_to='categories/', blank=True, null=True, verbose_name="Image", help_text="Image de la catégorie")

    class Meta:
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"

    def save(self, *args, **kwargs):
        #Génère un slug unique à partir du nom si non renseigné.
        if not self.slug_cat:
            self.slug_cat = slugify(self.nom_cat)
            num = 1
            unique_slug = self.slug_cat
            while Category.objects.filter(slug_cat=unique_slug).exists():
                unique_slug = f'{self.slug_cat}-{num}'
                num += 1
            self.slug_cat = unique_slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom_cat

    @property
    def icon(self):
        #Retourne une icône FontAwesome basée sur le slug de la catégorie.
        for key, icon in self.CATEGORY_ICONS.items():
            if self.slug_cat and key in self.slug_cat:
                return icon
        return 'fa-tag'

# Choix prédéfinis
BRAND_CHOICES = [
    ('APPLE', 'Apple'),
    ('SAMSUNG', 'Samsung'),
    ('HUAWEI', 'Huawei'),
    ('XIAOMI', 'Xiaomi'),
    ('GOOGLE', 'Google'),
    ('SONY', 'Sony'),
    ('LG', 'LG'),
    ('ITEL', 'Itel'),
    ('TECNO', 'Tecno'),
    ('INFINIX', 'Infinix'),
    ('HP', 'HP'),
    ('DELL', 'Dell'),
    ('LENOVO', 'Lenovo'),
    ('ASUS', 'Asus'),
    ('ACER', 'Acer'),
    ('MSI', 'MSI'),
    ('MICROSOFT', 'Microsoft'),
    ('AUTRE', 'Autre'),
]

COLOR_CHOICES = [
    ('Noir', 'Noir'), ('Blanc', 'Blanc'), ('Gris', 'Gris'), ('Rouge', 'Rouge'),
    ('Bleu', 'Bleu'), ('Vert', 'Vert'), ('Jaune', 'Jaune'), ('Rose', 'Rose'),
    ('Or', 'Or'), ('Argent', 'Argent'), ('Bronze', 'Bronze'), ('Violet', 'Violet'),
    ('Titanium Naturel', 'Titanium Naturel'), ('Titanium Noir', 'Titanium Noir'),
    ('Titanium Blanc', 'Titanium Blanc'), ('Titanium Désert', 'Titanium Désert'),
    ('Lumière Stellaire', 'Lumière Stellaire'), ('Minuit', 'Minuit'),
    ('Mauve', 'Mauve'), ('Graphite', 'Graphite'), ('Bleu Pacifique', 'Bleu Pacifique'),
    ('Bleu Sierra', 'Bleu Sierra'), ('Vert Alpin', 'Vert Alpin'),
    ('Violet Intense', 'Violet Intense'), ('Autre', 'Autre'),
]

COLOR_CODES = {
    'Noir': '#1a1a1a',
    'Blanc': '#f5f5f5',
    'Gris': '#808080',
    'Rouge': '#e53e3e',
    'Bleu': '#3182ce',
    'Vert': '#38a169',
    'Jaune': '#d69e2e',
    'Rose': '#ed64a6',
    'Or': '#d4af37',
    'Argent': '#a0aec0',
    'Bronze': '#cd7f32',
    'Violet': '#805ad5',
    'Titanium Naturel': '#BEBEBE',
    'Titanium Noir': '#2F2F2F',
    'Titanium Blanc': '#F2F2F2',
    'Titanium Désert': '#D2B48C',
    'Lumière Stellaire': '#F5F5DC',
    'Minuit': '#191970',
    'Mauve': '#E0B0FF',
    'Graphite': '#383838',
    'Bleu Pacifique': '#0E4D92',
    'Bleu Sierra': '#6996AD',
    'Vert Alpin': '#507672',
    'Violet Intense': '#4B0082',
    'Autre': '#CCCCCC',
}

CAPACITY_CHOICES = [
    ('32Go', '32 Go'), ('64Go', '64 Go'), ('128Go', '128 Go'), ('256Go', '256 Go'),
    ('512Go', '512 Go'), ('1To', '1 To'), ('2To', '2 To'), ('Autre', 'Autre'),
]

# Produit (modèle-mère)
class Product(models.Model):
    #Modèle représentant un produit (modèle de téléphone).
    # Les prix, couleurs, capacités et stocks sont gérés par les variantes.

    nom_prod = models.CharField(max_length=200, verbose_name="Nom du produit", default='')
    groupe_id = models.SlugField(max_length=200, blank=True, help_text="Slug unique du produit (auto-généré)")
    cat_id = models.ForeignKey(
        Category, on_delete=models.SET_NULL, null=True,
        related_name="products", verbose_name="Catégorie"
    )
    marque = models.CharField(max_length=50, blank=True, null=True, verbose_name="Marque")
    # imei = models.charfield(max_length=50,verbose_name="IMEI")
    description = models.TextField(blank=True, verbose_name="Description")
    specs = models.TextField(blank=True, verbose_name="Spécifications")

    is_active = models.BooleanField(default=True, verbose_name="Actif")
    is_2ndmain = models.BooleanField(default=False, verbose_name="Seconde main")
    fast_deal = models.BooleanField(default=False, verbose_name="Fast Deal")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.groupe_id:
            self.groupe_id = slugify(self.nom_prod.split('-')[0].strip())
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nom_prod

    # Propriétés calculées
    @property
    def stock_total(self):
        #Stock total = somme des stocks de toutes les variantes actives.
        return sum(v.stock for v in self.variants.filter(is_active=True))

    @property
    def stk_dla(self):
        return sum(v.stock_douala for v in self.variants.filter(is_active=True))

    @property
    def stk_yde(self):
        return sum(v.stock_yaounde for v in self.variants.filter(is_active=True))

    @property
    def is_in_stock(self):
        return self.stock_total > 0

    @property
    def default_variant(self):
        #Première variante active (utilisée pour afficher le prix dans les listings).
        return self.variants.filter(is_active=True).first()

    @property
    def default_price(self):
        v = self.default_variant
        return v.prix_unit if v else None

    @property
    def main_image(self):
        #Image principale (marquée is_primary ou première de la liste).
        img = self.images.filter(is_primary=True).first()
        if not img:
            img = self.images.first()
        return img

    @property
    def avg_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        count = reviews.count()
        if count > 0:
            total = sum(r.rating for r in reviews)
            return round(float(total) / count, 1)
        return None

    def get_absolute_url(self):
        return reverse('catalog:product_detail', args=[self.pk])

    # Compat: retourne le prix par défaut pour les templates existants
    @property
    def prix_unit(self):
        return self.default_price

    # Compat: retourne le code couleur de la première variante
    @property
    def color_code(self):
        v = self.default_variant
        if v and v.couleur:
            return COLOR_CODES.get(v.couleur, '#CCCCCC')
        return 'transparent'

    # Compat: retourne l'image pour les anciens templates
    @property
    def img_path(self):
        img = self.main_image
        return img.image if img else None

# Images du produit (galerie globale)
class ProductImage(models.Model):
    #Images globales liées à un produit (galerie).
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images', verbose_name="Produit")
    image = models.ImageField(upload_to='products/images/', verbose_name="Image")
    alt_text = models.CharField(max_length=200, blank=True, verbose_name="Texte alternatif")
    is_primary = models.BooleanField(default=False, verbose_name="Image principale")
    order = models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")

    class Meta:
        verbose_name = "Image Produit"
        verbose_name_plural = "Images Produit"
        ordering = ['order', 'id']

    def __str__(self):
        return f"Image {self.id} - {self.product.nom_prod}"

    def save(self, *args, **kwargs):
        # Si marquée principale, démarquer les autres images du même produit
        if self.is_primary:
            ProductImage.objects.filter(product=self.product, is_primary=True).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

# Variante produit (couleur + capacité + prix + stock)
class ProductVariant(models.Model):
    #Variante d'un produit : combinaison unique couleur + capacité avec son propre prix et stock.
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants', verbose_name="Produit")
    couleur = models.CharField(max_length=50, choices=COLOR_CHOICES, blank=True, null=True, verbose_name="Couleur")
    capacite = models.CharField(max_length=50, choices=CAPACITY_CHOICES, blank=True, null=True, verbose_name="Capacité")
    prix_unit = models.DecimalField(max_digits=12, decimal_places=0, verbose_name="Prix (FCFA)")
    image = models.ImageField(upload_to='products/variants/', blank=True, null=True, verbose_name="Image variante")
    is_active = models.BooleanField(default=True, verbose_name="Active")

    class Meta:
        verbose_name = "Variante"
        verbose_name_plural = "Variantes"
        unique_together = [('product', 'couleur', 'capacite')]
        ordering = ['capacite', 'couleur']

    def __str__(self):
        parts = [self.product.nom_prod]
        if self.couleur:
            parts.append(self.get_couleur_display())
        if self.capacite:
            parts.append(self.get_capacite_display())
        return " - ".join(parts)

    @property
    def stock(self):
        """Retourne le stock total toutes boutiques confondues."""
        return sum(s.quantity for s in self.stocks.all())

    @property
    def is_in_stock(self):
        return self.stock > 0

    @property
    def stock_douala(self):
        s = self.stocks.filter(store__city__icontains='Douala').first()
        return s.quantity if s else 0

    @property
    def stock_yaounde(self):
        s = self.stocks.filter(store__city__icontains='Yaoundé').first()
        if not s:
             s = self.stocks.filter(store__city__icontains='Yaounde').first()
        return s.quantity if s else 0

    @property
    def color_code(self):
        if self.couleur:
            return COLOR_CODES.get(self.couleur, '#CCCCCC')
        return 'transparent'

    @property
    def label(self):
        parts = []
        if self.couleur:
            parts.append(self.get_couleur_display())
        if self.capacite:
            parts.append(self.get_capacite_display())
        return " / ".join(parts) if parts else "Standard"

class VariantStock(models.Model):
    """Stock spécifique d'une variante dans une boutique particulière."""
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name='stocks', verbose_name="Variante")
    store = models.ForeignKey(Store, on_delete=models.CASCADE, related_name='stocks', verbose_name="Boutique")
    quantity = models.PositiveIntegerField(default=0, verbose_name="Quantité")

    class Meta:
        verbose_name = "Stock Boutique"
        verbose_name_plural = "Stocks Boutiques"
        unique_together = ['variant', 'store']

    def __str__(self):
        return f"{self.variant} - {self.store} ({self.quantity})"

# Avis clients
class ProductReview(models.Model):
    """Avis et notations laissés par les clients."""
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
        unique_together = ['product', 'user']

    def __str__(self):
        return f"Avis de {self.user.username} sur {self.product.nom_prod}"