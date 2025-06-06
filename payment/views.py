from rest_framework import status, generics, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from .models import (
    BillingAddress, Order, PaymentCard,
    CartItem, Cart, ShippingMethod, Discount
)
from store.models import Product
from .serializers import (
    BillingAddressSerializer, OrderSerializer, PaymentCardSerializer,
    ProductSerializer, CartItemSerializer, CartSerializer, ShippingMethodSerializer,
    DiscountSerializer, DiscountCodeValidationSerializer, CheckoutSerializer,
    ProductSearchSerializer, ContactSerializer
)
import uuid


class BillingAddressViewSet(viewsets.ModelViewSet):
    """ViewSet for managing billing addresses"""
    serializer_class = BillingAddressSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BillingAddress.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # If this is set as default, unset other defaults
        if serializer.validated_data.get('is_default', False):
            BillingAddress.objects.filter(user=self.request.user, is_default=True).update(is_default=False)
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # If this is set as default, unset other defaults
        if serializer.validated_data.get('is_default', False):
            BillingAddress.objects.filter(user=self.request.user, is_default=True).exclude(id=self.get_object().id).update(is_default=False)
        serializer.save()

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set billing address as default"""
        address = self.get_object()
        BillingAddress.objects.filter(user=request.user, is_default=True).update(is_default=False)
        address.is_default = True
        address.save()
        return Response({'status': 'default address set'})


class PaymentCardViewSet(viewsets.ModelViewSet):
    """ViewSet for managing payment cards"""
    serializer_class = PaymentCardSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return PaymentCard.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        # If this is set as default, unset other defaults
        if serializer.validated_data.get('is_default', False):
            PaymentCard.objects.filter(user=self.request.user, is_default=True).update(is_default=False)
        serializer.save(user=self.request.user)

    def perform_update(self, serializer):
        # If this is set as default, unset other defaults
        if serializer.validated_data.get('is_default', False):
            PaymentCard.objects.filter(user=self.request.user, is_default=True).exclude(id=self.get_object().id).update(is_default=False)
        serializer.save()

    @action(detail=True, methods=['post'])
    def set_default(self, request, pk=None):
        """Set payment card as default"""
        card = self.get_object()
        PaymentCard.objects.filter(user=request.user, is_default=True).update(is_default=False)
        card.is_default = True
        card.save()
        return Response({'status': 'default card set'})


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for products (read-only)"""
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        return Product.objects.filter(is_active=True)

    def list(self, request, *args, **kwargs):
        """List products with search and filtering"""
        search_serializer = ProductSearchSerializer(data=request.query_params)
        search_serializer.is_valid(raise_exception=True)
        
        queryset = self.get_queryset()
        
        # Apply filters
        search = search_serializer.validated_data.get('search')
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) | Q(description__icontains=search)
            )
        
        min_price = search_serializer.validated_data.get('min_price')
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        
        max_price = search_serializer.validated_data.get('max_price')
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        category = search_serializer.validated_data.get('category')
        if category:
            queryset = queryset.filter(category__icontains=category)
        
        # Apply ordering
        ordering = search_serializer.validated_data.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        # Paginate results
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class CartAPIView(APIView):
    """API view for cart management"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user's cart"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        serializer = CartSerializer(cart)
        return Response(serializer.data)

    def post(self, request):
        """Add item to cart"""
        cart, created = Cart.objects.get_or_create(user=request.user)
        
        serializer = CartItemSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        product_id = serializer.validated_data['product_id']
        quantity = serializer.validated_data['quantity']
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product_id=product_id,
            defaults={'quantity': quantity}
        )
        
        if not created:
            # Update quantity if item already exists
            cart_item.quantity += quantity
            cart_item.save()
        
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data, status=status.HTTP_201_CREATED)

    def put(self, request):
        """Update cart item quantity"""
        cart = get_object_or_404(Cart, user=request.user)
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        
        if not item_id or not quantity:
            return Response({'error': 'item_id and quantity are required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.quantity = quantity
        cart_item.save()
        
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data)

    def delete(self, request):
        """Remove item from cart"""
        cart = get_object_or_404(Cart, user=request.user)
        item_id = request.data.get('item_id')
        
        if not item_id:
            return Response({'error': 'item_id is required'}, 
                          status=status.HTTP_400_BAD_REQUEST)
        
        cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
        cart_item.delete()
        
        cart_serializer = CartSerializer(cart)
        return Response(cart_serializer.data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def clear_cart(request):
    """Clear all items from cart"""
    cart = get_object_or_404(Cart, user=request.user)
    cart.items.all().delete()
    
    cart_serializer = CartSerializer(cart)
    return Response(cart_serializer.data)


class ShippingMethodListView(generics.ListAPIView):
    """List available shipping methods"""
    serializer_class = ShippingMethodSerializer
    permission_classes = [AllowAny]
    queryset = ShippingMethod.objects.filter(is_active=True)


class DiscountValidationView(APIView):
    """Validate discount codes"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Validate discount code"""
        serializer = DiscountCodeValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        discount = serializer.validated_data['discount_code']
        discount_serializer = DiscountSerializer(discount)
        
        # Calculate discount amount for user's cart
        cart = get_object_or_404(Cart, user=request.user)
        cart_total = sum(item.product.price * item.quantity for item in cart.items.all())
        
        discount_amount = 0
        if discount.discount_type == 'percentage':
            discount_amount = cart_total * (discount.discount_value / 100)
        else:
            discount_amount = min(discount.discount_value, cart_total)
        
        return Response({
            'discount': discount_serializer.data,
            'discount_amount': discount_amount,
            'new_total': cart_total - discount_amount
        })


class CheckoutView(APIView):
    """Handle checkout process"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Process checkout"""
        serializer = CheckoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        cart = get_object_or_404(Cart, user=user)
        
        if not cart.items.exists():
            return Response({'error': 'Cart is empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get or create billing address
        billing_address = None
        if serializer.validated_data.get('billing_address_id'):
            billing_address = get_object_or_404(
                BillingAddress, 
                id=serializer.validated_data['billing_address_id'], 
                user=user
            )
        elif serializer.validated_data.get('new_billing_address'):
            billing_serializer = BillingAddressSerializer(
                data=serializer.validated_data['new_billing_address']
            )
            billing_serializer.is_valid(raise_exception=True)
            billing_address = billing_serializer.save(user=user)
        
        # Get shipping method
        shipping_method = get_object_or_404(
            ShippingMethod, 
            id=serializer.validated_data['shipping_method_id'],
            is_active=True
        )
        
        # Get or create payment card (if card payment)
        payment_card = None
        if serializer.validated_data['payment_method'] == 'card':
            if serializer.validated_data.get('payment_card_id'):
                payment_card = get_object_or_404(
                    PaymentCard,
                    id=serializer.validated_data['payment_card_id'],
                    user=user
                )
            elif serializer.validated_data.get('new_payment_card'):
                card_serializer = PaymentCardSerializer(
                    data=serializer.validated_data['new_payment_card']
                )
                card_serializer.is_valid(raise_exception=True)
                payment_card = card_serializer.save(user=user)
        
        # Get discount if provided
        discount = None
        if serializer.validated_data.get('discount_code'):
            discount = Discount.objects.get(
                code__iexact=serializer.validated_data['discount_code']
            )
        
        # Calculate totals
        subtotal = sum(item.product.price * item.quantity for item in cart.items.all())
        discount_amount = 0
        if discount:
            if discount.discount_type == 'percentage':
                discount_amount = subtotal * (discount.discount_value / 100)
            else:
                discount_amount = min(discount.discount_value, subtotal)
        
        shipping_cost = shipping_method.price
        total_amount = subtotal - discount_amount + shipping_cost
        
        # Create order
        order = Order.objects.create(
            user=user,
            order_number=str(uuid.uuid4())[:8].upper(),
            billing_address=billing_address,
            shipping_method=shipping_method,
            discount=discount,
            subtotal=subtotal,
            discount_amount=discount_amount,
            shipping_cost=shipping_cost,
            total_amount=total_amount,
            payment_method=serializer.validated_data['payment_method'],
            status='pending'
        )
        
        # Copy cart items to order
        for cart_item in cart.items.all():
            order.items.create(
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.product.price
            )
        
        # Update discount usage if applied
        if discount:
            discount.used_count += 1
            discount.save()
        
        # Clear cart
        cart.items.all().delete()
        
        # Here you would typically integrate with payment processor
        # For now, we'll just mark as processing
        order.status = 'processing'
        order.save()
        
        order_serializer = OrderSerializer(order)
        return Response(order_serializer.data, status=status.HTTP_201_CREATED)


class OrderViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing orders"""
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(user=self.request.user).order_by('-created_at')


class ContactView(APIView):
    """Handle contact form submissions"""
    permission_classes = [AllowAny]

    def post(self, request):
        """Submit contact form"""
        serializer = ContactSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Send email (configure your email settings)
        try:
            send_mail(
                subject=f"Contact Form: {serializer.validated_data['subject']}",
                message=f"""
                Name: {serializer.validated_data['name']}
                Email: {serializer.validated_data['email']}
                
                Message:
                {serializer.validated_data['message']}
                """,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.CONTACT_EMAIL],
                fail_silently=False,
            )
            
            return Response({'message': 'Contact form submitted successfully'})
        except Exception as e:
            return Response(
                {'error': 'Failed to send message. Please try again later.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


# Additional utility views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_dashboard_data(request):
    """Get user dashboard data"""
    user = request.user
    
    # Get user's recent orders
    recent_orders = Order.objects.filter(user=user).order_by('-created_at')[:5]
    
    # Get saved addresses and cards count
    addresses_count = BillingAddress.objects.filter(user=user).count()
    cards_count = PaymentCard.objects.filter(user=user).count()
    
    # Get cart items count
    cart, created = Cart.objects.get_or_create(user=user)
    cart_items_count = sum(item.quantity for item in cart.items.all())
    
    return Response({
        'recent_orders': OrderSerializer(recent_orders, many=True).data,
        'addresses_count': addresses_count,
        'cards_count': cards_count,
        'cart_items_count': cart_items_count,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def site_statistics(request):
    """Get site statistics for admin dashboard"""
    if not request.user.is_staff:
        return Response({'error': 'Unauthorized'}, status=status.HTTP_403_FORBIDDEN)
    
    from django.db.models import Count, Sum
    from datetime import datetime, timedelta
    
    # Get statistics
    total_orders = Order.objects.count()
    total_revenue = Order.objects.aggregate(Sum('total_amount'))['total_amount__sum'] or 0
    total_users = User.objects.count()
    total_products = Product.objects.count()
    
    # Recent statistics (last 30 days)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    recent_orders = Order.objects.filter(created_at__gte=thirty_days_ago).count()
    recent_revenue = Order.objects.filter(created_at__gte=thirty_days_ago).aggregate(
        Sum('total_amount'))['total_amount__sum'] or 0
    
    # Top products
    top_products = Product.objects.annotate(
        order_count=Count('cartitem__order')
    ).order_by('-order_count')[:5]
    
    return Response({
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'total_users': total_users,
        'total_products': total_products,
        'recent_orders': recent_orders,
        'recent_revenue': recent_revenue,
        'top_products': ProductSerializer(top_products, many=True).data,
    })