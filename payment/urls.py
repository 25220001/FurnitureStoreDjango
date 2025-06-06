from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'billing-addresses', views.BillingAddressViewSet, basename='billing-address')
router.register(r'payment-cards', views.PaymentCardViewSet, basename='payment-card')
router.register(r'products', views.ProductViewSet, basename='product')
router.register(r'orders', views.OrderViewSet, basename='order')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Cart management
    path('cart/', views.CartAPIView.as_view(), name='cart'),
    path('cart/clear/', views.clear_cart, name='clear-cart'),
    
    # Shipping methods
    path('shipping-methods/', views.ShippingMethodListView.as_view(), name='shipping-methods'),
    
    # Discount validation
    path('validate-discount/', views.DiscountValidationView.as_view(), name='validate-discount'),
    
    # Checkout
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    
    # Contact form
    path('contact/', views.ContactView.as_view(), name='contact'),
    
    # Dashboard and statistics
    path('dashboard/', views.user_dashboard_data, name='user-dashboard'),
    path('admin/statistics/', views.site_statistics, name='site-statistics'),
]

# Alternative URL patterns with more descriptive names
app_name = 'ecommerce'

# If you prefer more RESTful nested URLs, you can also use:
"""
Alternative URL structure (uncomment if preferred):

urlpatterns = [
    # Authentication required endpoints
    path('user/', include([
        # Billing addresses
        path('billing-addresses/', views.BillingAddressViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }), name='billing-address-list'),
        path('billing-addresses/<int:pk>/', views.BillingAddressViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }), name='billing-address-detail'),
        path('billing-addresses/<int:pk>/set-default/', views.BillingAddressViewSet.as_view({
            'post': 'set_default'
        }), name='billing-address-set-default'),
        
        # Payment cards
        path('payment-cards/', views.PaymentCardViewSet.as_view({
            'get': 'list',
            'post': 'create'
        }), name='payment-card-list'),
        path('payment-cards/<int:pk>/', views.PaymentCardViewSet.as_view({
            'get': 'retrieve',
            'put': 'update',
            'patch': 'partial_update',
            'delete': 'destroy'
        }), name='payment-card-detail'),
        path('payment-cards/<int:pk>/set-default/', views.PaymentCardViewSet.as_view({
            'post': 'set_default'
        }), name='payment-card-set-default'),
        
        # Orders
        path('orders/', views.OrderViewSet.as_view({
            'get': 'list'
        }), name='order-list'),
        path('orders/<int:pk>/', views.OrderViewSet.as_view({
            'get': 'retrieve'
        }), name='order-detail'),
        
        # Cart
        path('cart/', views.CartAPIView.as_view(), name='cart'),
        path('cart/clear/', views.clear_cart, name='clear-cart'),
        
        # Dashboard
        path('dashboard/', views.user_dashboard_data, name='dashboard'),
    ])),
    
    # Public endpoints
    path('products/', views.ProductViewSet.as_view({
        'get': 'list'
    }), name='product-list'),
    path('products/<int:pk>/', views.ProductViewSet.as_view({
        'get': 'retrieve'
    }), name='product-detail'),
    
    path('shipping-methods/', views.ShippingMethodListView.as_view(), name='shipping-methods'),
    path('contact/', views.ContactView.as_view(), name='contact'),
    
    # Checkout process
    path('validate-discount/', views.DiscountValidationView.as_view(), name='validate-discount'),
    path('checkout/', views.CheckoutView.as_view(), name='checkout'),
    
    # Admin endpoints
    path('admin/statistics/', views.site_statistics, name='admin-statistics'),
]
"""