
from django import forms
from .models import Product,Images,Banner,Offer,Category,Brand
import re




class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price','categories', 'brand']
        widgets = {
        'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
        'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        'price': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Price'}),
        # 'stock': forms.Select(attrs={'class': 'form-control'}),
        # 'status': forms.Select(attrs={'class': 'form-control'}),
        'brand': forms.Select(attrs={'class': 'form-control'}),
        'categories': forms.Select(attrs={'class': 'form-control'}),
       
    }
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        # Filter valid offers
        self.fields['categories'].queryset  = Category.objects.filter(is_available=True)    
        self.fields['brand'].queryset       = Brand.objects.filter(is_block=False)    
    

class CategoryForm(forms.ModelForm) :
    class Meta:
        model = Category
        fields = ['name','description']
        widgets = {
        'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
        'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }
   


class CategoryOfferForm(forms.ModelForm) :
    class Meta:
        model   = Category
        fields  = ['offer']
        widgets = {
            'offer': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super(CategoryOfferForm, self).__init__(*args, **kwargs)
        # Filter valid offers
        self.fields['offer'].queryset = Offer.objects.filter(is_block=False)   


class ProductOfferForm(forms.ModelForm) :
    class Meta:
        model   = Product
        fields  = ['offer'] 
        widgets = {
            'offer': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super(ProductOfferForm, self).__init__(*args, **kwargs)
        # Filter valid offers
        self.fields['offer'].queryset = Offer.objects.filter(is_block=False)


class ImageForm(forms.ModelForm):
    class Meta:
        model = Images
        fields = ['image']


class BannerForm(forms.ModelForm) :
    class Meta :
        model = Banner    
        fields = ['title','subtitle_1','subtitle_2','banner']   
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'title'}),
            'subtitle_1': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'subtitle 1'}),
            'subtitle_2': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'subtitle 2'}),
            'banner': forms.FileInput(attrs={'class': 'form-control-file'}),
        } 


class OfferForm(forms.ModelForm) :
    class Meta :
        model = Offer
        fields = ['title','description','discount_percentage','end_date']

        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            # 'discount_type': forms.Select(attrs={'class': 'form-control'}),
            'discount_percentage': forms.TextInput(attrs={'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'placeholder': 'YYYY-MM-DD'}),
        }
        input_formats = {
            'end_date': ['%Y-%m-%d'],
        }
       