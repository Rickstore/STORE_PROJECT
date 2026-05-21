from django.contrib import admin
from django.utils.html import format_html
from .models import Store, Category, Product, ProductVariant, VariantStock, ProductImage, ProductReview
from .forms import ProductAdminForm


@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'address')
    list_filter = ('city',)
    search_fields = ('name', 'city')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('nom_cat', 'slug_cat')
    prepopulated_fields = {'slug_cat': ('nom_cat',)}
    search_fields = ('nom_cat',)


# ---------------------------------------------------------------------------
# Inlines pour le ProductAdmin
# ---------------------------------------------------------------------------

class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    max_num = 10
    fields = ('image', 'alt_text', 'is_primary', 'order', 'thumbnail_preview')
    readonly_fields = ('thumbnail_preview',)
    ordering = ('order',)

    def thumbnail_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:60px;border-radius:4px;" />', obj.image.url)
        return "—"
    thumbnail_preview.short_description = "Aperçu"


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1
    fields = ('couleur', 'capacite', 'prix_unit', 'image', 'is_active')
    ordering = ('capacite', 'couleur')


# ---------------------------------------------------------------------------
# Admin Produit
# ---------------------------------------------------------------------------

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    form = ProductAdminForm
    inlines = [ProductImageInline, ProductVariantInline]

    list_display = (
        'nom_prod', 'marque', 'cat_id',
        'display_stock_total', 'display_variant_count', 'is_active'
    )
    list_filter = ('is_active', 'cat_id', 'marque', 'is_2ndmain', 'fast_deal')
    list_editable = ('is_active',)
    prepopulated_fields = {'groupe_id': ('nom_prod',)}
    search_fields = ('nom_prod', 'groupe_id', 'specs', 'description')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Informations Générales', {
            'fields': ('nom_prod', 'groupe_id', ('marque', 'autre_marque'), 'cat_id')
        }),
        ('Description & Specs', {
            'fields': ('description', 'specs'),
            'classes': ('collapse',),
        }),
        ('Statut', {
            'fields': ('is_active', 'is_2ndmain', 'fast_deal', 'created_at')
        }),
    )

    def display_stock_total(self, obj):
        total = obj.stock_total
        color = '#27ae60' if total > 0 else '#e74c3c'
        return format_html('<b style="color:{};">{}</b>', color, total)
    display_stock_total.short_description = "Stock total"

    def display_variant_count(self, obj):
        count = obj.variants.filter(is_active=True).count()
        return format_html('<span style="color:#2980b9;">{} variante(s)</span>', count)
    display_variant_count.short_description = "Variantes"


# ---------------------------------------------------------------------------
# Admin Variante (accès direct si besoin)
# ---------------------------------------------------------------------------

class VariantStockInline(admin.TabularInline):
    model = VariantStock
    extra = 2

@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    inlines = [VariantStockInline]
    list_display = ('product', 'couleur', 'capacite', 'prix_unit', 'display_stock_dla', 'display_stock_yde', 'is_active')
    list_filter = ('is_active', 'couleur', 'capacite', 'product__cat_id')
    list_editable = ('prix_unit', 'is_active')
    search_fields = ('product__nom_prod',)
    autocomplete_fields = ('product',)

    def display_stock_dla(self, obj):
        return obj.stock_douala
    display_stock_dla.short_description = "Stock Douala"

    def display_stock_yde(self, obj):
        return obj.stock_yaounde
    display_stock_yde.short_description = "Stock Yaoundé"


# ---------------------------------------------------------------------------
# Admin Avis
# ---------------------------------------------------------------------------

@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved')
    list_editable = ('is_approved',)
    search_fields = ('product__nom_prod', 'user__username', 'comment')
    readonly_fields = ('created_at',)
    actions = ['delete_selected']
