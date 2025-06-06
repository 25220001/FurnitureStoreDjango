from django.contrib import admin
from .models import (
    BillingAddress, ShippingMethod, Order, OrderItem, 
    PaymentCard, Cart, CartItem, Discount
)


@admin.register(BillingAddress)
class BillingAddressAdmin(admin.ModelAdmin):
    list_display = ('title_name', 'user', 'first_name', 'last_name', 'city', 'is_default')
    list_filter = ('is_default', 'state')
    search_fields = ('title_name', 'first_name', 'last_name', 'user__username')


@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'priority', 'price', 'is_active')
    list_filter = ('priority', 'is_active')
    list_editable = ('price', 'is_active')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'user', 'status', 'payment_completed', 'total', 'created_at')
    list_filter = ('status', 'payment_completed', 'created_at')
    search_fields = ('order_id', 'user__username')
    readonly_fields = ('order_id', 'created_at', 'updated_at')
    inlines = [OrderItemInline]


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')
    list_filter = ('order__status',)
    search_fields = ('order__order_id', 'product__name')


@admin.register(PaymentCard)
class PaymentCardAdmin(admin.ModelAdmin):
    list_display = ('user', 'card_last_four', 'card_type', 'is_default')
    list_filter = ('card_type', 'is_default')
    search_fields = ('user__username', 'cardholder_name')
    readonly_fields = ('payment_token',)


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'created_at')
    search_fields = ('user__username', 'session_key')
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('cart', 'product', 'quantity')
    search_fields = ('cart__user__username', 'product__name')


@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'is_active', 'valid_until')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code', 'description')
    list_editable = ('is_active',)