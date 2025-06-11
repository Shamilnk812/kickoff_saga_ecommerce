from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(Category)
admin.site.register(Brand)
admin.site.register(Product)
admin.site.register(Variants)
admin.site.register(Banner)
admin.site.register(Offer)

