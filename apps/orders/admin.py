from django.contrib import admin
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    raw_id_fields = ['product']
    extra = 0

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'client_id', 'statut', 'mt_total', 'pay_mode', 'date_com']
    list_filter = ['statut', 'pay_mode', 'date_com']
    search_fields = ['order_number', 'client_id__username', 'client_id__email']
    inlines = [OrderItemInline]
    
    fieldsets = (
        ('Informations Générales', {
            'fields': ('client_id', 'statut', 'mt_total', 'pay_mode')
        }),
    )

