
from django.urls import path
from . import views

urlpatterns = [
    # Main cart endpoints (matching your original structure)
    path('cart/', views.cart_summary_api, name='cart-summary'),          # GET - replaces cart_summary
    path('cart/add/', views.cart_add_api, name='cart-add'),              # POST - replaces cart_add
    path('cart/update/', views.cart_update_api, name='cart-update'),      # POST - replaces cart_update  
    path('cart/delete/', views.cart_delete_api, name='cart-delete'),      # POST - replaces cart_delete
    
    # Additional REST endpoints for React
    path('cart/full/', views.get_full_cart, name='cart-full'),           # GET - full cart data
    path('cart/clear/', views.clear_cart_api, name='cart-clear'),         # DELETE - clear cart
]
