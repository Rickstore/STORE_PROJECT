from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Address

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'phone', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('username', 'email', 'phone')
    ordering = ('-date_joined',)
    
    fieldsets = UserAdmin.fieldsets + (
        ('Informations Complémentaires', {'fields': ('role', 'phone')}),
    )
    
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'city', 'phone', 'created_at')
    list_filter = ('city',)
    search_fields = ('user__username', 'address', 'phone')
