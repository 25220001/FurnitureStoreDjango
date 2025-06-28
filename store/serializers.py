
# serializers.py
from rest_framework import serializers
from .models import Category, Color, Product, ProductImage, Review, Wishlist
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
        fields = ['image', 'alt_text', 'is_primary']


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
    reviews = ReviewSerializer(many=True, read_only=True)
    related_products = ProductListSerializer(many=True, read_only=True)
    average_rating = serializers.SerializerMethodField()
    review_count = serializers.SerializerMethodField()
    main_image = serializers.SerializerMethodField()
    glb_image = serializers.SerializerMethodField()
    images = serializers.SerializerMethodField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'price', 'main_image', 'glb_image',
            'description', 'category',
            'images', 'reviews', 'related_products',
            'average_rating', 'review_count', 'available_colors__hex_code',
        ]

    def get_average_rating(self, obj):
        reviews = obj.reviews.all()
        if reviews:
            return sum(review.rating for review in reviews) / len(reviews)
        return 0

    def get_review_count(self, obj):
        return obj.reviews.count()

    def get_main_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image and primary_image.image:
            request = self.context.get('request')
            return request.build_absolute_uri(primary_image.image.url) if request else primary_image.image.url
        return None

    def get_glb_image(self, obj):
        image = obj.images.filter(image__iendswith='.glb').first()
        if image and image.image:
            request = self.context.get('request')
            return request.build_absolute_uri(image.image.url) if request else image.image.url
        return None

    def get_images(self, obj):
        images = obj.images.exclude(
            image__iendswith='.glb').order_by('-is_primary')
        return ProductImageSerializer(images, many=True, context=self.context).data

    # def get_available_colors(self, obj):
    #     available_colors = obj.available_colors
    #     return Color(available_colors).hex_code


class WishlistSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ['id', 'product']


class ImageSearchSerializer(serializers.Serializer):
    image = serializers.FileField()  # Changed from ImageField to FileField
    top_k = serializers.IntegerField(default=5, min_value=1, max_value=20)

    def validate_image(self, value):
        """Validate that the uploaded file is a valid image"""
        from PIL import Image
        import io

        # Check file extension
        valid_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']
        if not any(value.name.lower().endswith(ext) for ext in valid_extensions):
            raise serializers.ValidationError(
                "Invalid image format. Supported formats: JPG, PNG, GIF, BMP, WebP")

        # Check if file can be opened as image
        try:
            # Reset file pointer
            value.seek(0)
            # Try to open and verify image
            with Image.open(io.BytesIO(value.read())) as img:
                img.verify()
            # Reset file pointer after verification
            value.seek(0)
        except Exception as e:
            raise serializers.ValidationError(f"Invalid image file: {str(e)}")

        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError(
                "Image file too large. Maximum size is 10MB")

        return value


class ColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Color
        fields = ['id', 'name', 'hex_code']


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    available_colors = ColorSerializer(many=True, read_only=True)
    effective_price = serializers.ReadOnlyField()
    discount_percentage = serializers.ReadOnlyField()
    average_rating = serializers.ReadOnlyField()
    review_count = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'price', 'sale_price', 'effective_price', 'discount_percentage',
            'sku', 'stock_quantity', 'condition', 'is_active', 'is_featured',
            'is_on_sale', 'is_best_seller', 'average_rating', 'review_count',
            'images', 'available_colors'
        ]
