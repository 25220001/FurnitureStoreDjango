from store.models import Product
from .models import Cart, CartItem
from django.shortcuts import get_object_or_404

def get_or_create_cart(user=None, session_key=None):
    """Get or create cart for user or guest session"""
    if user and user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=user)
    else:
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    return cart

def add_to_cart(cart, product_id, quantity):
    """Add item to cart or update quantity if exists"""
    product = get_object_or_404(Product, id=product_id)
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart, 
        product=product,
        defaults={'quantity': quantity}
    )
    
    if not created:
        cart_item.quantity = quantity
        cart_item.save()
    
    return cart_item

def remove_from_cart(cart, product_id):
    """Remove item from cart"""
    try:
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        cart_item.delete()
        return True
    except CartItem.DoesNotExist:
        return False

def update_cart_item(cart, product_id, quantity):
    """Update cart item quantity"""
    try:
        cart_item = CartItem.objects.get(cart=cart, product_id=product_id)
        cart_item.quantity = quantity
        cart_item.save()
        return cart_item
    except CartItem.DoesNotExist:
        return None

def clear_cart(cart):
    """Clear all items from cart"""
    cart.items.all().delete()