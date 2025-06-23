
# serializers.py
from rest_framework import serializers
from .models import Category, Product, ProductImage, Review, Wishlist
from django.contrib.auth.models import User

class CategorySerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'product_count']
    
    def get_product_count(self, obj):
        return obj.products.count()

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'color']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']

class ReviewSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Review
        fields = ['id', 'user', 'rating', 'comment', 'created_at']
        read_only_fields = ['id', 'created_at']

class ProductListSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    main_image = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'main_image',
            'category', 'average_rating', 'review_count'
        ]

    def get_main_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            request = self.context.get('request')
            return request.build_absolute_uri(primary_image.image.url) if request else primary_image.image.url
        return None

    def get_average_rating(self, obj):
        return obj.average_rating

    def get_review_count(self, obj):
        return obj.review_count

class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual product view"""
    category = CategorySerializer(read_only=True)
    gallery_images = ProductImageSerializer(many=True, read_only=True)
    reviews = ReviewSerializer(many=True, read_only=True)
    related_products = ProductListSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'main_image',
            'detailed_description', 'specifications', 'category',
            'gallery_images', 'reviews', 'related_products',
            'average_rating', 'review_count'
        ]
    
    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0
    
    def get_review_count(self, obj):
        return obj.reviews.count()

class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = Wishlist
        fields = ['id', 'product']