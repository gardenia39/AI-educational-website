from django.db import models
from django.contrib.auth.models import User
from base.models import BaseModel
from products.models import Product, Coupon
from django.conf import settings
import os

# Create your models here.


class Profile(BaseModel):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="profile")
    is_email_verified = models.BooleanField(default=False)
    email_token = models.CharField(max_length=100, null=True, blank=True)
    profile_image = models.URLField(max_length=500, blank=True, null=True)
    bio = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.user.username

    def get_cart_count(self):
        return CartItem.objects.filter(cart__is_paid=False, cart__user=self.user).count()


class Cart(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="cart", null=True, blank=True)
    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    is_paid = models.BooleanField(default=False)

    def get_cart_total(self):
        cart_items = self.cart_items.all()
        total_price = 0

        for cart_item in cart_items:
            total_price += cart_item.get_product_price()

        return total_price

    def get_cart_total_price_after_coupon(self):
        total = self.get_cart_total()

        if self.coupon and total >= self.coupon.minimum_amount:
            total -= self.coupon.discount_amount

        return total


class CartItem(BaseModel):
    cart = models.ForeignKey(
        Cart, on_delete=models.CASCADE, related_name="cart_items")
    product = models.ForeignKey(
        Product, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.IntegerField(default=1)

    def get_product_price(self):
        return self.product.price * self.quantity


class Order(BaseModel):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="orders")
    order_id = models.CharField(max_length=100, unique=True)
    order_date = models.DateTimeField(auto_now_add=True)
    payment_status = models.CharField(max_length=100)
    payment_mode = models.CharField(max_length=100)
    order_total_price = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(
        Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    grand_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Order {self.order_id} by {self.user.username}"

    def get_order_total_price(self):
        return self.order_total_price


class OrderItem(BaseModel):
    order = models.ForeignKey(
        Order, on_delete=models.CASCADE, related_name="order_items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.PositiveIntegerField(default=1)
    product_price = models.DecimalField(
        max_digits=10, decimal_places=2, null=True)

    def __str__(self):
        return f"{self.product.product_name} - {self.quantity}"

    def get_total_price(self):
        return self.product_price * self.quantity


class UserCourse(BaseModel):
    """记录用户购买/获取的课程，以及百度网盘发货状态"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='purchased_courses')
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='course_owners')
    is_delivered = models.BooleanField(
        default=False, verbose_name="是否已发送网盘链接")
    netdisk_link = models.URLField(
        max_length=500, blank=True, null=True, verbose_name="发给用户的百度网盘链接")
    netdisk_password = models.CharField(
        max_length=50, blank=True, null=True, verbose_name="提取码")
    delivered_at = models.DateTimeField(null=True, blank=True, verbose_name="发货时间")

    class Meta:
        unique_together = ('user', 'product')
        verbose_name = "用户课程"
        verbose_name_plural = "用户课程"

    def __str__(self):
        return f"{self.user.username} - {self.product.product_name}"
