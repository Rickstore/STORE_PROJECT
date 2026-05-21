from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('catalog/', views.CatalogView.as_view(), name='catalog'),
    path('product/<int:pk>/', views.ProductDetailView.as_view(), name='product_detail'),
    path('variant/<int:pk>/data/', views.variant_data, name='variant_data'),
    path('garantie/', views.GarantieView.as_view(), name='garantie'),
]
