from django.urls import path
from . import views

urlpatterns = [
    # Main store endpoints

    path('', views.hello_view),
    path('products/', views.ProductListView.as_view(), name='product-list'),
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('products/<slug:slug>/',
         views.ProductDetailView.as_view(), name='product-detail'),
    path('categories/<slug:category_slug>/products/',
         views.category_products, name='category-products'),

    # Review endpoints
    path('products/<slug:product_slug>/reviews/',
         views.add_product_review, name='add-product-review'),

    # Wishlist endpoints (requires authentication)
    path('wishlist/', views.WishlistView.as_view(), name='wishlist'),
    path('wishlist/<int:pk>/', views.WishlistDeleteView.as_view(),
         name='wishlist-delete'),

    path('api/product-assistant-stream/', views.product_assistant_stream,
         name='product_assistant_stream'),
    path('api/search/image/', views.ImageSearchView.as_view(), name='image_search'),
    path('admin/refresh-features/',
         views.RefreshFeaturesView.as_view(), name='refresh_features'),
]
