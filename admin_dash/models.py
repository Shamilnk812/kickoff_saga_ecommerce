from django.db import models
from django.utils import timezone
from PIL import Image
# Create your models here.


class Offer(models.Model) :
    title = models.CharField(max_length=255)
    description = models.TextField(default='New Offer')
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    discount_percentage = models.DecimalField(max_digits=10, decimal_places=2)
    is_block = models.BooleanField(default=False)
    is_valid = models.BooleanField(default=True)

    # def is_valid(self):
    #     now = timezone.now()
    #     return self.start_date <= now <= self.end_date 

    def save(self, *args, **kwargs):
        # Automatically update is_valid based on the condition
        if self.end_date < self.start_date:
            self.is_valid = False

        super().save(*args, **kwargs)   
    
    def __str__(self) -> str:
        return self.title
    

class Category(models.Model) :
    name = models.CharField(max_length=150)
    description = models.TextField(max_length=250,default='Product description')
    offer = models.ForeignKey(Offer, on_delete=models.SET_NULL, blank=True, null=True)
    is_available = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.name

    

class Brand(models.Model) :
    name = models.CharField(max_length=100)
    is_block = models.BooleanField(default=False)

    def __str__(self) -> str:
        return self.name




class Product(models.Model) : 
    name = models.CharField( max_length=200, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField(null=True, blank=True)
    created_date = models.DateTimeField( default=timezone.now)
    categories = models.ForeignKey(Category,on_delete=models.CASCADE)
    is_available = models.BooleanField(default=True)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)
    offer = models.ForeignKey(Offer, on_delete=models.SET_NULL, blank=True, null=True)

    def discounted_price(self):
        discounted_price = self.price
        if self.offer and self.offer.is_valid and self.offer.discount_percentage:
            discounted_price -= (self.price * self.offer.discount_percentage / 100)

        return max(discounted_price, 0)
    
    def offer_save_amount(self):
        original_price = self.price
        discounted_price = self.discounted_price()
        return max(original_price - discounted_price, 0)
    
    def __str__(self) -> str:
        return self.name
    

class Images(models.Model) :
    image = models.ImageField(upload_to='product_images/img')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    class Meta:
        verbose_name = 'photo'
        verbose_name_plural = 'photos'   

class Variants(models.Model) :
    size = models.FloatField(blank=True, null=True)
    quantity = models.IntegerField(default=0)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)


class Banner(models.Model) :
    title = models.CharField(max_length=150,null=True)
    subtitle_1 = models.CharField(max_length=200,null=True)
    subtitle_2 = models.CharField(max_length=200,null=True)
    banner = models.ImageField(upload_to='banner/img')
    is_available = models.BooleanField(default=True)
    
   