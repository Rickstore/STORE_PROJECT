from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total', 'delivery_type', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at', 'delivery_type']
    search_fields = ['order_number', 'user__username', 'user__email']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('user', 'status', 'total', 'payment_status')
        }),
        ('Livraison', {
            'fields': ('delivery_type', 'store', 'address', 'assigned_delivery')
        }),
    )
