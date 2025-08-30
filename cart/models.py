
from django.db import models
from admin_dash.models import Product,Variants
from django.contrib.auth.models import User
from .models import * 
from decimal import Decimal
from datetime import timedelta, date
# Create your models here.


class Coupon(models.Model) :
    coupon_code = models.CharField(max_length=150)
    minimum_amount = models.IntegerField(default=1000)
    discount_percentage = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)

    def calculate_discount(self, total):
        if total >= self.minimum_amount:
            return total * (Decimal(self.discount_percentage) / Decimal('100'))
        return 0


class UsedCoupon(models.Model) :
    used_coupon_code = models.CharField(max_length=150) 
    user = models.ForeignKey(User, on_delete=models.CASCADE)


class Cart(models.Model) :
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    coupon = models.ForeignKey(Coupon,on_delete=models.SET_NULL, null=True, blank=True)
    product_qty = models.IntegerField()
    size = models.FloatField(null=True,blank=True)
    created_at = models.DateField(auto_now_add=True)
    shipping_cost = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    @property
    def is_valid_cart_item(self):
        return (
            self.product.is_available and
            self.product.categories.is_available and
            self.product.brand.is_available
        )
    
    @property
    def total_cost(self):
        if not self.is_valid_cart_item:
            return 0
        product_price = self.product.discounted_price() if self.product.offer and self.product.offer.is_valid else self.product.price
        return self.product_qty * product_price
    
    @property
    def is_in_stock(self):
        try:
            # Get the variant for this product and size
            variant = Variants.objects.get(product=self.product, size=self.size)
            return variant.quantity >= self.product_qty
        except Variants.DoesNotExist:
            return False  
    
    @classmethod
    def total_cost_for_user(cls, user):
        user_carts = cls.objects.filter(user=user)
        total = 0

        for cart in user_carts:
            if cart.is_valid_cart_item:
                total += cart.total_cost
        return total
    
    


class Order(models.Model) :
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    fname = models.CharField( max_length=150, null=False)
    lname = models.CharField( max_length=150, null=False)
    email = models.CharField( max_length=150, null=False)
    phone = models.CharField(max_length=50, null=False)
    address = models.TextField(null=False)
    city = models.CharField(max_length=150, null=False)
    state = models.CharField(max_length=150, null=False)
    country = models.CharField(max_length=150, null=False)
    pincode = models.CharField(max_length=50, null=False)
    total_price = models.FloatField(null=False)
    payment_mode = models.CharField(max_length=150, null=False)
    payment_id = models.CharField( max_length=250, null=True)
    message = models.TextField(null=True)
    tracking_no = models.CharField(max_length=150, null=True)
    updated_at = models.DateField( auto_now=True)
    created_at = models.DateField(auto_now_add=True)
    return_reason = models.TextField(null=True)
    cancel_reason = models.TextField(null=True)
    coupon_discount_amount = models.FloatField(null=True)
    offer_discount_amount = models.FloatField(null=True)
    shipping_type = models.CharField(max_length=50, default='free-shipping')
    shipping_amount = models.FloatField(default=0)
    


class OrderItem(models.Model) :
    order    = models.ForeignKey(Order, on_delete=models.CASCADE)
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    price    = models.FloatField(null=False)
    quantity = models.IntegerField(null=False)
    size     = models.FloatField(null=False,default=0)
    offer_saved_amount = models.FloatField(null=True, blank=True)
    updated_at = models.DateField(auto_now=True)
    created_at = models.DateField(auto_now_add=True) 
    
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Confirmed','Confirmed'),
        ('Out for Shipping', 'Out for Shipping'),
        ('Shipped', 'Shipped'),
        ('Out for Delivery', 'Out for Delivery'),
        ('Delivered', 'Delivered'),
        ('Return Requested', 'Return Requested'),
        ('Return Rejected', 'Return Rejected'),
        ('Returned', 'Returned'),
        ('Cancelled', 'Cancelled'),
    )
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pending')
    cancel_reason = models.TextField(null=True, blank=True)
    return_reason = models.TextField(null=True, blank=True)
    return_valid_until = models.DateField(null=True, blank=True)
    cancelled_by = models.CharField(null=True, blank=True)
    
    
    @property
    def total_price(self):
        return self.price * self.quantity
    
    @property
    def can_return(self):
        if self.return_valid_until:
            return date.today() <= self.return_valid_until
        return False
    


class Wishlist(models.Model) :
    user       = models.ForeignKey(User, on_delete=models.CASCADE)    
    product    = models.ForeignKey(Product,on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
    
    @property
    def is_valid_wishlist_item(self):
        return (
            self.product.is_available and
            self.product.categories.is_available and
            self.product.brand.is_available
        )