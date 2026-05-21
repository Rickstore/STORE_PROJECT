from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='index'),
    path('products/', views.AdminProductListView.as_view(), name='products'),
    path('products/add/', views.ProductCreateView.as_view(), name='product_create'),
    path('products/<int:pk>/edit/', views.ProductUpdateView.as_view(), name='product_edit'),
    path('categories/', views.CategoryListView.as_view(), name='categories'),
    path('categories/<int:pk>/edit/', views.CategoryUpdateView.as_view(), name='category_edit'),

    path('orders/', views.AdminOrderListView.as_view(), name='orders'),
    path('orders/<str:order_number>/', views.AdminOrderDetailView.as_view(), name='order_detail'),
    path('users/', views.AdminUserListView.as_view(), name='users'),
    path('livreurs/', views.LivreurListView.as_view(), name='livreur_list'),
    path('livreurs/add/', views.LivreurCreateView.as_view(), name='add_livreur'),
    path('livreurs/<int:pk>/edit/', views.LivreurUpdateView.as_view(), name='edit_livreur'),
    path('livreurs/<int:pk>/delete/', views.LivreurDeleteView.as_view(), name='delete_livreur'),
    path('livreurs/<int:pk>/encaisser/', views.EncaisserSoldeView.as_view(), name='encaisser_solde'),
    path('stock/', views.AdminStockView.as_view(), name='stock'),
    path('reviews/', views.AdminReviewListView.as_view(), name='reviews'),
    path('reviews/<int:pk>/<str:action>/', views.AdminReviewActionView.as_view(), name='review_action'),
    path('reports/sales/', views.SalesReportView.as_view(), name='sales_report'),
]
