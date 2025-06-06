from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils import timezone


class TimeStampedModel(models.Model):
    """Abstract base model with timestamp fields"""
    
    created_at = models.DateTimeField(default=timezone.now)

    updated_at = models.DateTimeField(default=timezone.now)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    """Category model for furniture types (e.g., Chairs, Tables, Sofas)"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    # Parent category for hierarchical structure
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('category_detail', kwargs={'slug': self.slug})

    @property
    def is_parent(self):
        return self.children.exists()


class Brand(TimeStampedModel):
    """Brand model for furniture manufacturers"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Material(models.Model):
    """Material model for furniture materials (e.g., Wood, Metal, Fabric)"""
    name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name


class Color(models.Model):
    """Color model for furniture colors"""
    name = models.CharField(max_length=50, unique=True)
    hex_code = models.CharField(max_length=7, blank=True, help_text="Hex color code (e.g., #FF5733)")

    def __str__(self):
        return self.name


class Size(models.Model):
    """Size model for furniture sizes"""
    name = models.CharField(max_length=50, unique=True)  # e.g., Small, Medium, Large, XL
    description = models.CharField(max_length=100, blank=True)
    # Add ordering for proper size sequence
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Store(TimeStampedModel):
    """Store/Branch model for preferred store selection"""
    name = models.CharField(max_length=100)
    address = models.TextField()
    city = models.CharField(max_length=50)
    phone_number = models.CharField(max_length=20)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True)
    # Add operating hours
    opening_hours = models.CharField(max_length=200, blank=True, help_text="e.g., Mon-Fri: 9AM-9PM")

    def __str__(self):
        return f"{self.name} - {self.city}"


class UserProfile(TimeStampedModel):
    """Extended user profile model"""
    GENDER_CHOICES = [
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True)
    date_of_birth = models.DateField(blank=True, null=True)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    preferred_store = models.ForeignKey(Store, on_delete=models.SET_NULL, null=True, blank=True)
    newsletter_subscribed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"

    @property
    def full_name(self):
        return f"{self.user.first_name} {self.user.last_name}".strip()


class Address(TimeStampedModel):
    """User addresses model for shipping/billing"""
    ADDRESS_TYPES = [
        ('shipping', 'Shipping'),
        ('billing', 'Billing'),
        ('both', 'Both'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    full_name = models.CharField(max_length=100)
    address_line_1 = models.CharField(max_length=200)
    address_line_2 = models.CharField(max_length=200, blank=True)
    governorate = models.CharField(max_length=50)  # For Egyptian addresses
    district = models.CharField(max_length=50, blank=True)
    city = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    address_type = models.CharField(max_length=20, choices=ADDRESS_TYPES, default='both')
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Addresses'
        # Ensure only one default address per type per user
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'address_type', 'is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_address_per_type'
            )
        ]

    def __str__(self):
        return f"{self.full_name} - {self.governorate}, {self.city}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Ensure only one default address per type
            Address.objects.filter(
                user=self.user, 
                address_type=self.address_type,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Product(TimeStampedModel):
    """Main Product model for furniture items"""
    CONDITION_CHOICES = [
        ('new', 'New'),
        ('refurbished', 'Refurbished'),
        ('used', 'Used'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    
    # Relationships
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='products')
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True)
    materials = models.ManyToManyField(Material, blank=True)
    available_colors = models.ManyToManyField(Color, blank=True, related_name='products')
    available_sizes = models.ManyToManyField(Size, blank=True, related_name='products')
    
    # Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sale_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    
    # Product details
    sku = models.CharField(max_length=100,unique=True)
    weight = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="Weight in kg")
    dimensions_length = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="Length in cm")
    dimensions_width = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="Width in cm")
    dimensions_height = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True, help_text="Height in cm")
    
    # Inventory
    stock_quantity = models.PositiveIntegerField(default=0)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    condition = models.CharField(max_length=20, choices=CONDITION_CHOICES, default='new')
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    is_on_sale = models.BooleanField(default=False)
    is_best_seller = models.BooleanField(default=False)
    
    # SEO
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.CharField(max_length=300, blank=True)
    
    # Additional fields for better inventory management
    min_order_quantity = models.PositiveIntegerField(default=1)
    max_order_quantity = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_featured', 'is_active']),
            models.Index(fields=['sku']),
            models.Index(fields=['price']),
        ]

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('product_detail', kwargs={'slug': self.slug})

    @property
    def effective_price(self):
        """Return sale price if available, otherwise regular price"""
        return self.sale_price if self.sale_price else self.price

    @property
    def is_in_stock(self):
        """Check if product is in stock"""
        return self.stock_quantity > 0

    @property
    def is_low_stock(self):
        """Check if product stock is low"""
        return self.stock_quantity <= self.low_stock_threshold

    @property
    def discount_percentage(self):
        """Calculate discount percentage if on sale"""
        if self.sale_price and self.price > self.sale_price:
            return round(((self.price - self.sale_price) / self.price) * 100)
        return 0

    @property
    def average_rating(self):
        """Calculate average rating from reviews"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating'], 1)
        return 0

    @property
    def review_count(self):
        """Get total number of approved reviews"""
        return self.reviews.filter(is_approved=True).count()

    def clean(self):
        """Custom validation"""
        from django.core.exceptions import ValidationError
        if self.sale_price and self.sale_price >= self.price:
            raise ValidationError('Sale price must be less than regular price')


class ProductImage(TimeStampedModel):
    """Product images model"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'created_at']
        # Ensure only one primary image per product
        constraints = [
            models.UniqueConstraint(
                fields=['product', 'is_primary'],
                condition=models.Q(is_primary=True),
                name='unique_primary_image_per_product'
            )
        ]

    def __str__(self):
        return f"{self.product.name} - Image {self.order}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            # Ensure only one primary image per product
            ProductImage.objects.filter(
                product=self.product, 
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class ProductVariant(models.Model):
    """Product variants for different colors and sizes"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    color = models.ForeignKey(Color, on_delete=models.CASCADE, null=True, blank=True)
    size = models.ForeignKey(Size, on_delete=models.CASCADE, null=True, blank=True)
    sku = models.CharField(max_length=50 , unique=True)  # Make variant SKU unique
    price_adjustment = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['product', 'color', 'size']

    def __str__(self):
        variant_name = self.product.name
        if self.color:
            variant_name += f" - {self.color}"
        if self.size:
            variant_name += f" - {self.size}"
        return variant_name

    @property
    def effective_price(self):
        base_price = self.product.sale_price or self.product.price
        return base_price + self.price_adjustment

    @property
    def is_in_stock(self):
        return self.stock_quantity > 0


class Review(TimeStampedModel):
    """Product reviews model"""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200, blank=True)
    comment = models.TextField()
    is_verified_purchase = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=True)
    helpful_count = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['product', 'user']
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.product.name} - {self.rating} stars by {self.user.username}"


class Wishlist(models.Model):
    """User wishlist model - matches the heart icons in your design"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ['user', 'product']

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class SavedDesign(TimeStampedModel):
    """Saved designs/room layouts model"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_designs')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    design_data = models.JSONField()  # Store design configuration
    thumbnail = models.ImageField(upload_to='saved_designs/', blank=True, null=True)
    is_public = models.BooleanField(default=False)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.name}"


class Newsletter(models.Model):
    """Newsletter subscription model - for the email signup in footer"""
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email


class ContactMessage(TimeStampedModel):
    """Contact form messages model"""
    name = models.CharField(max_length=100)
    email = models.EmailField()
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Message from {self.name} - {self.subject}"


# Additional models you might need for a complete e-commerce system

class Tag(models.Model):
    """Tags for products (e.g., 'Modern', 'Vintage', 'Eco-friendly')"""
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(max_length=50, unique=True)

    def __str__(self):
        return self.name


# Add tags relationship to Product model
# In your Product model, add:
# tags = models.ManyToManyField(Tag, blank=True, related_name='products')


class ShippingZone(models.Model):
    """Shipping zones for delivery calculation"""
    name = models.CharField(max_length=100)
    governorates = models.JSONField()  # List of governorates covered
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2)
    free_shipping_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Coupon(TimeStampedModel):
    """Discount coupons"""
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES)
    discount_value = models.DecimalField(max_digits=8, decimal_places=2)
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_discount_amount = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    usage_limit = models.PositiveIntegerField(null=True, blank=True)
    used_count = models.PositiveIntegerField(default=0)
    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.code

    @property
    def is_valid(self):
        now = timezone.now()
        return self.is_active and self.valid_from <= now <= self.valid_until and (
            self.usage_limit is None or self.used_count < self.usage_limit
        )