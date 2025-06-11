from django.db import models
from django.contrib.auth.models import User

# Create your models here.


class Address(models.Model):
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
    message = models.TextField(null=True)
    created_at = models.DateField(auto_now_add=True)



class Wallet(models.Model) :
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    wallet = models.BigIntegerField(null=True)

