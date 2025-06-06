from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from .models import Category, Product, Review, Wishlist
from .serializers import (
    CategorySerializer, ProductListSerializer, ProductDetailSerializer,
    ReviewSerializer, WishlistSerializer
)

# GET /api/products/ - List all products (replaces store view)
class ProductListView(generics.ListAPIView):
    queryset = Product.objects.all().select_related('category').prefetch_related('reviews')
    serializer_class = ProductListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Add filtering options
        category = self.request.query_params.get('category', None)
        search = self.request.query_params.get('search', None)
        
        if category:
            queryset = queryset.filter(category__slug=category)
        if search:
            queryset = queryset.filter(name__icontains=search)
            
        return queryset

# GET /api/categories/ - List all categories
class CategoryListView(generics.ListAPIView):
    queryset = Category.objects.all().prefetch_related('product')
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]

# GET /api/products/<slug>/ - Get specific product (replaces product_info view)
class ProductDetailView(generics.RetrieveAPIView):
    queryset = Product.objects.all().select_related('category').prefetch_related(
        'gallery_images', 'reviews__user', 'related_products'
    )
    serializer_class = ProductDetailSerializer
    lookup_field = 'slug'
    permission_classes = [AllowAny]

# GET /api/categories/<slug>/products/ - Get products by category (replaces list_category view)
@api_view(['GET'])
@permission_classes([AllowAny])
def category_products(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)
    products = Product.objects.filter(category=category).select_related('category').prefetch_related('reviews')
    
    category_data = CategorySerializer(category).data
    products_data = ProductListSerializer(products, many=True).data
    
    return Response({
        'category': category_data,
        'products': products_data,
        'total_products': products.count()
    })

# Additional useful endpoints for your React app

# POST /api/products/<slug>/reviews/ - Add review to product
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_product_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug)
    
    # Check if user already reviewed this product
    if Review.objects.filter(product=product, user=request.user).exists():
        return Response(
            {'error': 'You have already reviewed this product'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = ReviewSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(product=product, user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# GET/POST /api/wishlist/ - Get user's wishlist or add to wishlist
class WishlistView(generics.ListCreateAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user).select_related('product')
    
    def perform_create(self, serializer):
        product_id = self.request.data.get('product_id')
        product = get_object_or_404(Product, id=product_id)
        
        # Check if already in wishlist
        if Wishlist.objects.filter(user=self.request.user, product=product).exists():
            return Response(
                {'error': 'Product already in wishlist'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer.save(user=self.request.user, product=product)

# DELETE /api/wishlist/<id>/ - Remove from wishlist
class WishlistDeleteView(generics.DestroyAPIView):
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(user=self.request.user)