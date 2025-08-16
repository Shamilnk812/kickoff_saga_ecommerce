
from django import forms
from .models import *
from cart.models import Coupon
import re
from django.utils import timezone



# ------------- Product Form --------------

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'description', 'price','categories', 'brand']
        widgets = {
        'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Product name'}),
        'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        'price': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Price'}),
        'brand': forms.Select(attrs={'class': 'form-control'}),
        'categories': forms.Select(attrs={'class': 'form-control'}),
       
    }
    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        # Filter valid offers
        self.fields['categories'].queryset  = Category.objects.filter(is_available=True)    
        self.fields['brand'].queryset       = Brand.objects.filter(is_block=False)    
    

    def clean_name(self):
        """
        Validate and clean the 'name' field for a product.
        This method enforces the following validation rules:
        Trims leading/trailing spaces and reduces multiple spaces to a single space.
        Allows only letters , numbers, spaces, and the '&' character.
        Length must be between 2 and 50 characters. 
        Product name cannot start with '&' and Consecutive '&' characters (e.g., '&&') are not allowed.
        Product name cannot consist of only digits and name cannot consist of only special characters.
        Product name must be unique (case-insensitive), excluding the current instance.
        """         
        name = self.cleaned_data.get('name', '').strip()
        # Remove multiple spaces between words
        name = re.sub(r'\s+', ' ', name)
        if not re.match(r'^[A-Za-z0-9\s&]+$', name):
            raise forms.ValidationError("Brand name can only contain letters, numbers, spaces, '&'. No special characters allowed.")
        if len(name) < 2 or len(name) > 50:
            raise forms.ValidationError("Product name must be between 2 and 50 characters.")
        if name.lstrip().startswith('&'):
             raise forms.ValidationError("Name cannot start with '&'.")
        if '&&' in name:
            raise forms.ValidationError("Name cannot contain consecutive '&' characters.")
        if name.isdigit():
            raise forms.ValidationError("Product name cannot be only numbers.")
        if re.fullmatch(r'[\W_]+', name):
            raise forms.ValidationError("Product name cannot contain only special characters.")
        if Product.objects.filter(name__iexact=name).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("A product with this name already exists.")

        return name

    def clean_price(self):
        price = self.cleaned_data.get('price')
        if not price:
            raise forms.ValidationError("Price is required. Please add a positive price")
        if not price >= 1:
            raise forms.ValidationError("Price must be a valid number.")

        return int(price)

    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()
        description = re.sub(r'\s+', ' ', description)
        if len(description) < 10:
            raise forms.ValidationError("Product descripton must be atleast 10 characters")
          # Allowed characters: letters, numbers, spaces, hyphen, ampersand
        if not re.match(r'^[A-Za-z0-9\s&\-.]+$', description):
            raise forms.ValidationError("Product name contains invalid characters.")
    
        return description

    def clean_categories(self):
        category = self.cleaned_data.get('categories')
        if not category:
            raise forms.ValidationError("Category is required.")
        return category

    def clean_brand(self):
        brand = self.cleaned_data.get('brand')
        if not brand:
            raise forms.ValidationError("Brand is required.")
        return brand
    


#-------------- Category Form ------------

class CategoryForm(forms.ModelForm) :
    class Meta:
        model = Category
        fields = ['name','description']
        widgets = {
        'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Category name'}),
        'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean_name(self):
        name = self.cleaned_data['name']
        name = re.sub(r'\s+', ' ', name)
        category_id = self.instance.id if self.instance and self.instance.id else None

        if name.isdigit():
            raise forms.ValidationError("Enter a valid name")
        
        if len(name.strip()) < 3:
            raise forms.ValidationError("Category name should be at least 3 characters long.")
        
        if Category.objects.exclude(id=category_id).filter(name=name).exists():
            raise forms.ValidationError("Category with this name already exists!")

        return name

    def clean_description(self):
        description = self.cleaned_data['description']
        if description.isdigit():
            raise forms.ValidationError("Enter a valid description")
        if len(description.strip()) < 10:
            raise forms.ValidationError("Description should be at least 10 characters long. Please provide more details.")
        
        return description
   


# ------------ Brand Form ------------

class BrandForm(forms.ModelForm):
    class Meta:
        model = Brand
        fields = ['name']
        widgets = {
        'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter brand name'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        name = re.sub(r'\s+', ' ', name)
        brand_id = self.instance.id if self.instance and self.instance.id else None

        if not name:
            raise forms.ValidationError("Brand name cannot be empty.")
        
        if name.isdigit():
            raise forms.ValidationError("Brand name should not be entirely numeric.")
        
        if not re.match(r'^[A-Za-z0-9\s&-]+$', name):
            raise forms.ValidationError("Brand name can only contain letters, numbers, spaces, '&', and '-'. No special characters allowed.")
        
        if len(name) < 2 or len(name) > 50:
            raise forms.ValidationError("Brand name must be between 2 and 50 characters.")

        if Brand.objects.exclude(id=brand_id).filter(name__iexact=name).exists():
            raise forms.ValidationError("A brand with this name already exists.")
        return name




class ProductSizeVariantsForm(forms.ModelForm):
    size = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter size'}))
    quantity = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter quantity'}))

    class Meta:
        model = Variants
        fields = ['size', 'quantity']
       
    
    def clean_size(self):
        size = self.cleaned_data.get('size')
        product = self.initial.get('product')  
        current_variant_id = self.instance.pk  
       
        if size is None:
            raise forms.ValidationError("Size is required.")
        
        try:
            size = float(size)
        except (ValueError, TypeError):
            raise forms.ValidationError("Size must be a number.")
        if size < 1 or size > 16:
            raise forms.ValidationError("Enter a valid size between 1 and 16.")
        if size and product:
            qs = Variants.objects.filter(product=product, size=size)
            if current_variant_id:
                qs = qs.exclude(pk=current_variant_id)  
            
            if qs.exists():
                raise forms.ValidationError(f"A variant with size {size} already exists for this product.")
        return size

    
    def clean_quantity(self):
        quantity = self.cleaned_data.get('quantity')
        
        if quantity is None:
            raise forms.ValidationError("Quantity is required.")
        
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            raise forms.ValidationError("Quantity must be a valid number.")
        
        if quantity < 0:
            raise forms.ValidationError("Quantity cannot be negative.")
        
        if quantity > 500:
            raise forms.ValidationError("You can add only up to 500 stock.")

        return quantity
    

        

# --------- Coupon Form ---------

class CouponForm(forms.ModelForm):
    
    coupon_code = forms.CharField( widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Coupon code'}))
    minimum_amount = forms.CharField( widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter minimum amount'}))
    discount_percentage = forms.CharField( widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter discount percentage'}))
    class Meta:
        model = Coupon
        fields = ['coupon_code', 'minimum_amount', 'discount_percentage']
     
    def clean_coupon_code(self):
        code = self.cleaned_data.get('coupon_code', '').strip()

        if not code:
            raise forms.ValidationError("Coupon code is required.")
        
        if code.isdigit():
            raise forms.ValidationError("Coupon code cannot contain only numbers.")
        
        if Coupon.objects.filter(coupon_code__iexact=code).exists():
            raise forms.ValidationError("Coupon already exists.")
        
        return code

    def clean_minimum_amount(self):
        min_amount = self.cleaned_data.get('minimum_amount')
        try:
            min_amount = int(min_amount)
        except (ValueError, TypeError):
            raise forms.ValidationError("Minimum amount must be a valid number.")
            
        if min_amount is None or min_amount <= 0:
            raise forms.ValidationError("Enter a valid minimum amount.")
        
        return min_amount

    def clean_discount_percentage(self):
        discount = self.cleaned_data.get('discount_percentage')
        try:
            discount = int(discount)
        except (ValueError, TypeError):
            raise forms.ValidationError("Discount percentage must be a valid number.")

        if discount is None or discount < 5 or discount > 25:
            raise forms.ValidationError("Enter a valid discount percentage (5% to 25%).")
        
        return discount




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
        now = timezone.now()
        self.fields['offer'].queryset = Offer.objects.filter(is_block=False, start_date__lte=now, end_date__gte=now)  
    
    def clean_offer(self):
        offer = self.cleaned_data.get('offer')
        if not offer:
            raise forms.ValidationError('Offer is required. Please add valid one')
        if not Offer.objects.filter(pk=offer.pk).exists():
            raise forms.ValidationError('Offer is not valid')
        return offer




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
        now = timezone.now()
        self.fields['offer'].queryset = Offer.objects.filter(is_block=False , start_date__lte=now, end_date__gte=now)
    
    def clean_offer(self):
        offer = self.cleaned_data.get('offer')
        if not offer:
            raise forms.ValidationError('Offer is required. Please add valid one')
        if not Offer.objects.filter(pk=offer.pk).exists():
            raise forms.ValidationError('Offer is not valid')
        return offer


class ImageForm(forms.ModelForm):
    class Meta:
        model = Images
        fields = ['image']



# ------------ Banner --------------
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
    
    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        if not title:
            raise forms.ValidationError("Banner title is required.")
        if title.isdigit():
            raise forms.ValidationError("Banner title cannot be only numbers.")
        if re.match(r'^[^A-Za-z0-9]+$', title):
            raise forms.ValidationError("Banner title cannot be only special characters.")
        if len(title) < 3:
            raise forms.ValidationError("Banner title must be at least 3 characters long.")
        return title

    def clean_subtitle_1(self):
        subtitle_1 = self.cleaned_data.get('subtitle_1', '').strip()
        if subtitle_1:
            if subtitle_1.isdigit():
                raise forms.ValidationError("Subtitle 1 cannot be only numbers.")
            if re.match(r'^[^A-Za-z0-9]+$', subtitle_1):
                raise forms.ValidationError("Subtitle 1 cannot be only special characters.")
        return subtitle_1

    def clean_subtitle_2(self):
        subtitle_2 = self.cleaned_data.get('subtitle_2', '').strip()
        if subtitle_2:
            if subtitle_2.isdigit():
                raise forms.ValidationError("Subtitle 2 cannot be only numbers.")
            if re.match(r'^[^A-Za-z0-9]+$', subtitle_2):
                raise forms.ValidationError("Subtitle 2 cannot be only special characters.")
        return subtitle_2

    def clean(self):
        cleaned_data = super().clean()
        subtitle_1 = cleaned_data.get('subtitle_1', '').strip()
        subtitle_2 = cleaned_data.get('subtitle_2', '').strip()

        if subtitle_1 and subtitle_2 and subtitle_1.lower() == subtitle_2.lower():
            self.add_error('subtitle_2', "Subtitle 1 and Subtitle 2 must be different.")

        return cleaned_data
    




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
    
    def clean_title(self):
        title = self.cleaned_data.get('title', '').strip()
        title = re.sub(r'\s+', ' ', title)
        if not title:
            raise forms.ValidationError("Offer name is required")
        if title.isdigit():
            raise forms.ValidationError("Offer name cannot contain only numbers.")
        if not re.match(r'^[A-Za-z0-9 ]+$', title):
            raise forms.ValidationError("Offer name cannot contain special characters.")
        if Offer.objects.filter(title__icontains=title).exists():
            raise forms.ValidationError("Offer with name already exist!")
        
        return title
    
    def clean_description(self):
        description = self.cleaned_data.get('description', '').strip()

        if not description:
            raise forms.ValidationError('Offer description is required')
        if description.isdigit():
            raise forms.ValidationError("Offer description cannot contain only numbers.")
        if not re.search(r'[A-Za-z0-9]', description):
            raise forms.ValidationError("Offer description cannot contain only special characters.")
        if len(description) < 10:
            raise forms.ValidationError("Offer descriptions is shot, Please add more detailed description")
        
        return description
        
    def clean_discount_percentage(self):
        discount_percentage = self.cleaned_data.get('discount_percentage')

        try:
            discount_percentage = float(discount_percentage)
        except (TypeError, ValueError):
            raise forms.ValidationError("Discount amount must be a valid number.")

        if discount_percentage < 0:
            raise forms.ValidationError("Enter a positive number.")
        if discount_percentage < 5 or discount_percentage > 75 :
            raise forms.ValidationError("Discount percentage must be between 5 to 75%.")

        return discount_percentage

    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        try:
            end_date.strftime('%Y-%m-%d')
        except (AttributeError, ValueError):
            raise forms.ValidationError("Invalid date format. Please use YYYY-MM-DD.")

        if end_date <= timezone.now():
            raise forms.ValidationError("End date must be greater than the current date and time.")

        return end_date
       