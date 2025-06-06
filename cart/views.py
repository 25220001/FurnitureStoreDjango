from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Sum, F
from store.models import Product
from payment.models import Cart, CartItem
from .serializers import CartSerializer, AddToCartSerializer, UpdateCartItemSerializer, CartItemSerializer

def get_or_create_cart(user, session_key):
    """Helper to get or create cart"""
    if user and user.is_authenticated:
        cart, created = Cart.objects.get_or_create(
            user=user,
            defaults={'session_key': session_key, 'created_at': timezone.now()}
        )
    else:
        cart, created = Cart.objects.get_or_create(
            session_key=session_key,
            user=None,
            defaults={'created_at': timezone.now()}
        )
    return cart

# GET /api/cart/ - Get current cart
@api_view(['GET'])
@permission_classes([AllowAny])
def cart_summary_api(request):
    """Get user's cart summary with all items using CartSerializer"""
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    cart = get_or_create_cart(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key
    )
    
    serializer = CartSerializer(cart)
    return Response(serializer.data)

# POST /api/cart/add/ - Add item to cart
@api_view(['POST'])
@permission_classes([AllowAny])
def cart_add_api(request):
    """Add item to cart using AddToCartSerializer validation"""
    # Handle both JSON and form data for backward compatibility
    if request.content_type == 'application/json':
        data = request.data
    else:
        data = {
            'product_id': request.POST.get('product_id'),
            'quantity': request.POST.get('product_quantity', 1)  # Note: using product_quantity for form compatibility
        }
    
    # Validate input using serializer
    serializer = AddToCartSerializer(data=data)
    if not serializer.is_valid():
        return Response({'error': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
    
    validated_data = serializer.validated_data
    product_id = validated_data['product_id']
    product_quantity = validated_data['quantity']
    
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    cart = get_or_create_cart(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key
    )
    
    try:
        product = get_object_or_404(Product, id=product_id)
        
        # Check if item already exists in cart
        cart_item, created = CartItem.objects.get_or_create(
            cart=cart,
            product=product,
            defaults={'quantity': product_quantity}
        )
        
        if not created:
            # Item exists, update quantity
            cart_item.quantity += product_quantity
            cart_item.save()
        
        # Refresh cart to get updated totals
        cart.refresh_from_db()
        
        return JsonResponse({
            "qty": cart.total_items,
            "message": "Item added to cart successfully",
            "total": str(cart.total_price),
            "item": CartItemSerializer(cart_item).data
        })
        
    except Product.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Failed to add item to cart'}, status=500)

# POST /api/cart/update/ - Update cart item
@api_view(['POST'])
@permission_classes([AllowAny])
def cart_update_api(request):
    """Update cart item quantity using UpdateCartItemSerializer"""
    # Handle both JSON and form data
    if request.content_type == 'application/json':
        product_id = request.data.get('product_id')
        quantity_data = {'quantity': request.data.get('product_quantity') or request.data.get('quantity')}
    else:
        product_id = request.POST.get('product_id')
        quantity_data = {'quantity': request.POST.get('product_quantity') or request.POST.get('quantity')}
    
    if not product_id:
        return JsonResponse({'error': 'Product ID required'}, status=400)
    
    # Validate quantity using serializer (but allow 0 for deletion)
    if quantity_data['quantity'] is not None:
        try:
            quantity = int(quantity_data['quantity'])
            if quantity < 0:
                return JsonResponse({'error': 'Quantity cannot be negative'}, status=400)
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Invalid quantity format'}, status=400)
    else:
        return JsonResponse({'error': 'Quantity required'}, status=400)
    
    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid product ID format'}, status=400)
    
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'error': 'No cart found'}, status=404)
    
    try:
        cart = Cart.objects.get(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        
        # Find cart item
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        
        if quantity == 0:
            # Remove item if quantity is 0
            cart_item.delete()
            message = "Item removed from cart"
        else:
            # Validate quantity with serializer for positive values
            if quantity > 0:
                update_serializer = UpdateCartItemSerializer(data={'quantity': quantity})
                if not update_serializer.is_valid():
                    return Response({'error': update_serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
            
            # Update quantity
            cart_item.quantity = quantity
            cart_item.save()
            message = "Cart updated successfully"
        
        # Refresh cart to get updated totals
        cart.refresh_from_db()
        
        return JsonResponse({
            "qty": cart.total_items,
            "total": str(cart.total_price),
            "message": message
        })
        
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        return JsonResponse({'error': 'Item not found in cart'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Failed to update cart'}, status=500)

# POST /api/cart/delete/ - Remove item from cart
@api_view(['POST'])
@permission_classes([AllowAny])
def cart_delete_api(request):
    """Remove item from cart"""
    # Handle both JSON and form data
    if request.content_type == 'application/json':
        product_id = request.data.get('product_id')
    else:
        product_id = request.POST.get('product_id')
    
    if not product_id:
        return JsonResponse({'error': 'Product ID required'}, status=400)
    
    try:
        product_id = int(product_id)
    except (ValueError, TypeError):
        return JsonResponse({'error': 'Invalid product ID'}, status=400)
    
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'error': 'No cart found'}, status=404)
    
    try:
        cart = Cart.objects.get(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        
        # Find and delete cart item
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        cart_item.delete()
        
        # Refresh cart to get updated totals
        cart.refresh_from_db()
        
        return JsonResponse({
            "qty": cart.total_items,
            "total": str(cart.total_price),
            "message": "Item removed from cart successfully"
        })
        
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        return JsonResponse({'error': 'Item not found in cart'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Failed to remove item from cart'}, status=500)

# GET /api/cart/full/ - Get complete cart data using serializers
@api_view(['GET'])
@permission_classes([AllowAny])
def get_full_cart(request):
    """Get complete cart data with all item details using CartSerializer"""
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    cart = get_or_create_cart(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key
    )
    
    # Use CartSerializer for consistent data structure
    serializer = CartSerializer(cart)
    return Response(serializer.data)

# DELETE /api/cart/clear/ - Clear entire cart
@api_view(['DELETE'])
@permission_classes([AllowAny])
def clear_cart_api(request):
    """Clear entire cart"""
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'error': 'No cart found'}, status=404)
    
    try:
        cart = Cart.objects.get(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        
        # Delete all cart items
        CartItem.objects.filter(cart=cart).delete()
        
        # Refresh cart
        cart.refresh_from_db()
        
        return JsonResponse({
            "qty": cart.total_items,
            "total": str(cart.total_price),
            "message": "Cart cleared successfully"
        })
        
    except Cart.DoesNotExist:
        return JsonResponse({'error': 'Cart not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': 'Failed to clear cart'}, status=500)

# GET /api/cart/count/ - Get cart item count only
@api_view(['GET'])
@permission_classes([AllowAny])
def cart_count_api(request):
    """Get just the cart item count for quick updates"""
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({"qty": 0})
    
    try:
        cart = Cart.objects.get(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        
        return JsonResponse({"qty": cart.total_items})
        
    except Cart.DoesNotExist:
        return JsonResponse({"qty": 0})

# POST /api/cart/bulk-add/ - Add multiple items at once
@api_view(['POST'])
@permission_classes([AllowAny])
def bulk_add_cart_api(request):
    """Add multiple items to cart in a single request"""
    items = request.data.get('items', [])
    
    if not items:
        return Response({'error': 'No items provided'}, status=status.HTTP_400_BAD_REQUEST)
    
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    cart = get_or_create_cart(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key
    )
    
    # Validate all items first
    serializers_list = []
    for item_data in items:
        serializer = AddToCartSerializer(data=item_data)
        if not serializer.is_valid():
            return Response({
                'error': f'Invalid data for item: {serializer.errors}'
            }, status=status.HTTP_400_BAD_REQUEST)
        serializers_list.append(serializer)
    
    # If all valid, add items
    added_items = []
    try:
        for serializer in serializers_list:
            validated_data = serializer.validated_data
            product_id = validated_data['product_id']
            quantity = validated_data['quantity']
            
            try:
                product = get_object_or_404(Product, id=product_id)
                
                cart_item, created = CartItem.objects.get_or_create(
                    cart=cart,
                    product=product,
                    defaults={'quantity': quantity}
                )
                
                if not created:
                    cart_item.quantity += quantity
                    cart_item.save()
                
                added_items.append({
                    'product_id': product_id,
                    'quantity': quantity,
                    'item_data': CartItemSerializer(cart_item).data
                })
                
            except Product.DoesNotExist:
                return Response({
                    'error': f'Product with ID {product_id} not found'
                }, status=status.HTTP_404_NOT_FOUND)
        
        # Refresh cart to get updated totals
        cart.refresh_from_db()
        
        return Response({
            "qty": cart.total_items,
            "total": str(cart.total_price),
            "added_items": added_items,
            "message": f"Successfully added {len(added_items)} items to cart"
        })
        
    except Exception as e:
        return Response({'error': 'Failed to add items to cart'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# GET /api/cart/item/{product_id}/ - Get specific cart item
@api_view(['GET'])
@permission_classes([AllowAny])
def get_cart_item_api(request, product_id):
    """Get specific cart item details"""
    session_key = request.session.session_key
    if not session_key:
        return JsonResponse({'error': 'No cart found'}, status=404)
    
    try:
        cart = Cart.objects.get(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key
        )
        
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        serializer = CartItemSerializer(cart_item)
        
        return Response(serializer.data)
        
    except (Cart.DoesNotExist, CartItem.DoesNotExist):
        return JsonResponse({'error': 'Item not found in cart'}, status=404)

# GET /api/cart/items/ - Get all cart items with detailed info
@api_view(['GET'])
@permission_classes([AllowAny])
def get_cart_items_api(request):
    """Get all cart items with detailed product information"""
    session_key = request.session.session_key
    if not session_key:
        request.session.create()
        session_key = request.session.session_key
    
    cart = get_or_create_cart(
        user=request.user if request.user.is_authenticated else None,
        session_key=session_key
    )
    
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
    serializer = CartItemSerializer(cart_items, many=True)
    
    return Response({
        'items': serializer.data,
        'cart_summary': {
            'total_items': cart.total_items,
            'total_price': str(cart.total_price)
        }
    })