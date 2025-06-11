
from django.db import models
from admin_dash.models import Product
from django.contrib.auth.models import User
from .models import * 
# Create your models here.


class Coupon(models.Model) :
    coupon_code = models.CharField(max_length=150)
    is_expired = models.BooleanField(default=False)
    discound_amount = models.IntegerField(default=100)
    minimum_amount = models.IntegerField(default=1000)


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
    def total_cost(self):
        product_price = self.product.discounted_price() if self.product.offer and self.product.offer.is_valid else self.product.price
        return self.product_qty * product_price

    @classmethod
    def total_cost_for_user(cls, user):
        user_carts = cls.objects.filter(user=user)
        return sum(cart.total_cost for cart in user_carts)
    
    # def total_saved_amount_for_products_with_offers(self):
    #     total_saved_amount = 0

    #     for cart_item in Cart.objects.filter(user=self.user, product__offer__is_valid=True):
    #         total_saved_amount += cart_item.product.offer_save_amount() * cart_item.product_qty

    #     return total_saved_amount

    # def total_saved_amount_for_products_with_offers(self):
    #     total_saved_amount = 0

    #     for cart_item in Cart.objects.filter(user=self.user, product__offer__is_valid=True):
    #         product_offer_save_amount = cart_item.product.offer_save_amount()
    #         print(f"Product: {cart_item.product.name}, Offer Save Amount: {product_offer_save_amount}")
    #         total_saved_amount += product_offer_save_amount * cart_item.product_qty

    #     print(f"Total Saved Amount: {total_saved_amount}")
    #     return total_saved_amount


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
    order_status = (
        ('Order Confirmed','Order Confirmed'),
        ('Out For Shipping','Out For Shipping'),
        ('Shipped','Shipped'),
        ('Out For Delivery','Out For Delivery'),
        ('Deliverd','Deliverd'),
        ('Cancel','Cancel')
    )
    status = models.CharField(max_length=150, choices=order_status, default='Order Confirmed')
    message = models.TextField(null=True)
    tracking_no = models.CharField(max_length=150, null=True)
    updated_at = models.DateField( auto_now=True)
    created_at = models.DateField(auto_now_add=True)
    return_reason = models.TextField(null=True)
    cancel_reason = models.TextField(null=True)
    coupon_discount_amount = models.FloatField(null=True)
    offer_discount_amount = models.FloatField(null=True)
    


class OrderItem(models.Model) :
    order    = models.ForeignKey(Order, on_delete=models.CASCADE)
    product  = models.ForeignKey(Product, on_delete=models.CASCADE)
    price    = models.FloatField(null=False)
    quantity = models.IntegerField(null=False)
    size     = models.FloatField(null=False,default=0)
    
    @property
    def total_price(self):
        return self.price * self.quantity
    

class Wishlist(models.Model) :
    user       = models.ForeignKey(User, on_delete=models.CASCADE)    
    product    = models.ForeignKey(Product,on_delete=models.CASCADE)
    created_at = models.DateField(auto_now_add=True)
