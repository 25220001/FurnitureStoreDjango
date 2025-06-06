from rest_framework import serializers
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from .models import (
    BillingAddress, Order, PaymentCard, 
    CartItem, Cart, ShippingMethod, Discount
)
from store.models import Product
import re
from datetime import datetime


class BillingAddressSerializer(serializers.ModelSerializer):
    """Serializer for billing address information"""
    
    class Meta:
        model = BillingAddress
        fields = [
            'id', 'title_name', 'first_name', 'last_name', 'company_name', 
            'tax_number', 'state', 'city', 'area', 'zip_code', 
            'street_name', 'phone_number', 'is_default', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate_phone_number(self, value):
        """Validate phone number format"""
        if not re.match(r'^\+?1?\d{9,15}$', value):
            raise serializers.ValidationError("Invalid phone number format")
        return value

    def validate_zip_code(self, value):
        """Validate ZIP code format"""
        if not re.match(r'^\d{5}(-\d{4})?$', value):
            raise serializers.ValidationError("Invalid ZIP code format")
        return value


class ShippingMethodSerializer(serializers.ModelSerializer):
    """Serializer for shipping methods"""
    display_name = serializers.SerializerMethodField()
    display_description = serializers.SerializerMethodField()
    
    class Meta:
        model = ShippingMethod
        fields = [
            'id', 'name', 'price', 'delivery_days_min', 'delivery_days_max',
            'priority', 'is_active', 'display_name', 'display_description'
        ]

    def get_display_name(self, obj):
        if obj.priority == 'express':
            return f"Express Delivery (Priority) - ${obj.price}"
        return f"Standard Delivery - ${obj.price}"

    def get_display_description(self, obj):
        time_unit = "business days" if obj.priority == 'express' else "business weeks"
        return f"Arrives within {obj.delivery_days_min} - {obj.delivery_days_max} {time_unit}."


class PaymentCardSerializer(serializers.ModelSerializer):
    """Serializer for payment card information"""
    card_number = serializers.CharField(max_length=19, write_only=True)
    expiry_date = serializers.CharField(max_length=5, write_only=True)
    cvv = serializers.CharField(max_length=4, write_only=True)
    card_last_four = serializers.CharField(read_only=True)
    card_type = serializers.CharField(read_only=True)
    
    class Meta:
        model = PaymentCard
        fields = [
            'id', 'cardholder_name', 'card_number', 'expiry_date', 'cvv',
            'card_last_four', 'card_type', 'is_default', 'created_at'
        ]
        read_only_fields = ['id', 'card_last_four', 'card_type', 'created_at']

    def validate_card_number(self, value):
        """Validate card number format"""
        card_number = value.replace(' ', '')
        if not re.match(r'^\d{13,19}$', card_number):
            raise serializers.ValidationError('Invalid card number format')
        return card_number

    def validate_expiry_date(self, value):
        """Validate expiry date"""
        if not re.match(r'^\d{2}/\d{2}$', value):
            raise serializers.ValidationError('Invalid expiry date format (MM/YY)')
        
        month, year = value.split('/')
        current_year = datetime.now().year % 100
        current_month = datetime.now().month
        
        if int(year) < current_year or (int(year) == current_year and int(month) < current_month):
            raise serializers.ValidationError('Card has expired')
        
        if int(month) < 1 or int(month) > 12:
            raise serializers.ValidationError('Invalid month')
            
        return value

    def validate_cvv(self, value):
        """Validate CVV"""
        if not re.match(r'^\d{3,4}$', value):
            raise serializers.ValidationError('CVV must be 3 or 4 digits')
        return value

    def create(self, validated_data):
        """Create payment card with encrypted data"""
        card_number = validated_data.pop('card_number')
        validated_data.pop('expiry_date')  # Don't store expiry
        validated_data.pop('cvv')  # Never store CVV
        
        # Store only last 4 digits and determine card type
        validated_data['card_last_four'] = card_number[-4:]
        validated_data['card_type'] = self.get_card_type(card_number)
        
        return super().create(validated_data)

    def get_card_type(self, card_number):
        """Determine card type from card number"""
        if card_number.startswith('4'):
            return 'Visa'
        elif card_number.startswith('5') or card_number.startswith('2'):
            return 'Mastercard'
        elif card_number.startswith('3'):
            return 'American Express'
        return 'Unknown'


class ProductSerializer(serializers.ModelSerializer):
    """Serializer for products"""
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'description', 'price', 'stock_quantity',
            'category', 'image', 'is_active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class CartItemSerializer(serializers.ModelSerializer):
    """Serializer for cart items"""
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = ['id', 'product', 'product_id', 'quantity', 'total_price', 'created_at']
        read_only_fields = ['id', 'created_at']

    def get_total_price(self, obj):
        return obj.product.price * obj.quantity

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Quantity must be at least 1")
        if value > 99:
            raise serializers.ValidationError("Quantity cannot exceed 99")
        return value

    def validate_product_id(self, value):
        try:
            product = Product.objects.get(id=value, is_active=True)
            if product.stock_quantity < 1:
                raise serializers.ValidationError("Product is out of stock")
            return value
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found")


class CartSerializer(serializers.ModelSerializer):
    """Serializer for shopping cart"""
    items = CartItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = ['id', 'items', 'total_items', 'total_price', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_total_items(self, obj):
        return sum(item.quantity for item in obj.items.all())

    def get_total_price(self, obj):
        return sum(item.product.price * item.quantity for item in obj.items.all())


class DiscountSerializer(serializers.ModelSerializer):
    """Serializer for discount codes"""
    is_valid_now = serializers.SerializerMethodField()
    
    class Meta:
        model = Discount
        fields = [
            'id', 'code', 'discount_type', 'discount_value', 'minimum_amount',
            'valid_from', 'valid_to', 'usage_limit', 'used_count', 'is_active', 'is_valid_now'
        ]
        read_only_fields = ['id', 'used_count', 'is_valid_now']

    def get_is_valid_now(self, obj):
        return obj.is_valid()


class DiscountCodeValidationSerializer(serializers.Serializer):
    """Serializer for validating discount codes"""
    discount_code = serializers.CharField(max_length=50)

    def validate_discount_code(self, value):
        try:
            discount = Discount.objects.get(code__iexact=value)
            if not discount.is_valid():
                raise serializers.ValidationError('This discount code is not valid or has expired')
            return discount
        except Discount.DoesNotExist:
            raise serializers.ValidationError('Invalid discount code')


class OrderSerializer(serializers.ModelSerializer):
    """Serializer for orders"""
    items = CartItemSerializer(many=True, read_only=True)
    billing_address = BillingAddressSerializer(read_only=True)
    shipping_method = ShippingMethodSerializer(read_only=True)
    discount = DiscountSerializer(read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'status', 'items', 'billing_address',
            'shipping_method', 'discount', 'subtotal', 'discount_amount',
            'shipping_cost', 'total_amount', 'payment_method', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'order_number', 'created_at', 'updated_at'
        ]


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout process"""
    billing_address_id = serializers.IntegerField(required=False)
    new_billing_address = BillingAddressSerializer(required=False)
    shipping_method_id = serializers.IntegerField()
    payment_method = serializers.ChoiceField(choices=[
        ('card', 'Debit/Credit Card'),
        ('paypal', 'PayPal'),
        ('wallet', 'Wallet'),
    ])
    payment_card_id = serializers.IntegerField(required=False)
    new_payment_card = PaymentCardSerializer(required=False)
    discount_code = serializers.CharField(max_length=50, required=False)
    privacy_policy_agreed = serializers.BooleanField()

    def validate(self, data):
        """Validate checkout data"""
        # Validate billing address
        if not data.get('billing_address_id') and not data.get('new_billing_address'):
            raise serializers.ValidationError("Either billing_address_id or new_billing_address is required")

        # Validate payment method
        if data['payment_method'] == 'card':
            if not data.get('payment_card_id') and not data.get('new_payment_card'):
                raise serializers.ValidationError("Payment card information is required for card payments")

        # Validate privacy policy agreement
        if not data.get('privacy_policy_agreed'):
            raise serializers.ValidationError("You must agree to the privacy policy to complete your order")

        return data

    def validate_shipping_method_id(self, value):
        try:
            shipping_method = ShippingMethod.objects.get(id=value, is_active=True)
            return value
        except ShippingMethod.DoesNotExist:
            raise serializers.ValidationError("Invalid shipping method")

    def validate_discount_code(self, value):
        if value:
            try:
                discount = Discount.objects.get(code__iexact=value)
                if not discount.is_valid():
                    raise serializers.ValidationError('This discount code is not valid or has expired')
                return value
            except Discount.DoesNotExist:
                raise serializers.ValidationError('Invalid discount code')
        return value


class ProductSearchSerializer(serializers.Serializer):
    """Serializer for product search and filtering"""
    search = serializers.CharField(max_length=200, required=False)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    category = serializers.CharField(max_length=100, required=False)
    ordering = serializers.ChoiceField(choices=[
        ('name', 'Name A-Z'),
        ('-name', 'Name Z-A'),
        ('price', 'Price Low-High'),
        ('-price', 'Price High-Low'),
        ('-created_at', 'Newest First'),
        ('created_at', 'Oldest First'),
    ], required=False)


class ContactSerializer(serializers.Serializer):
    """Serializer for contact form"""
    name = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    subject = serializers.CharField(max_length=200)
    message = serializers.CharField(max_length=1000)

    def validate_email(self, value):
        """Validate email format"""
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', value):
            raise serializers.ValidationError("Invalid email format")
        return value