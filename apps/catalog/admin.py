from django.contrib import admin
from .models import Store, Category, Product, ProductReview, ProductSpecification

@admin.register(Store)
class StoreAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'address')
    list_filter = ('city',)
    search_fields = ('name', 'city')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)

class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'brand', 'category', 'price', 'stock', 'is_active', 'created_at')
    list_filter = ('is_active', 'category', 'brand')
    list_editable = ('price', 'stock', 'is_active')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'brand', 'description')
    date_hierarchy = 'created_at'
    inlines = [ProductSpecificationInline]
    fieldsets = (
        ('Informations Générales', {
            'fields': ('name', 'slug', 'brand', 'category', 'description')
        }),
        ('Prix & Stock', {
            'fields': ('price', 'stock', 'is_active')
        }),
        ('Média', {
            'fields': ('image',)
        }),
    )


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved')
    list_editable = ('is_approved',)
    search_fields = ('product__name', 'user__username', 'comment')
    readonly_fields = ('created_at',)
    actions = ['delete_selected']
