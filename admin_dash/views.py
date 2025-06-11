import io
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from .models import *
from cart.models import Order,OrderItem,Coupon
from django.contrib import messages
from .forms import *
from account_user.models import Wallet
from .models import Product,Images
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from django.urls import reverse
from django.db import transaction
from django.db.models import Sum,Count,F
from django.utils import timezone
from datetime import timedelta,datetime
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from .helpers import render_to_pdf
from django.db.models.functions import TruncMonth,TruncDay
from PIL import Image, ImageFilter
# from PIL import Image
# from io import BytesIO
# from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import JsonResponse





# -------------- Admin auth --------------

def admin_log_in(request) :
    if request.method == 'POST' :
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username.strip()=='' or password.strip()=='':
            messages.error(request, 'Fields cannot be empty!')
            return redirect('admin_log_in')
        user = authenticate(username=username,password=password)
        if user is not None :
            if user.is_active :
                if user.is_superuser :
                    login(request, user)
                    return redirect('dash_board')
                else:
                    messages.error(request, 'Sorry only admin is allowed to ') 
                    return redirect('admin_log_in')   
            else :
                messages.warning(request, 'Your account has been blocked')   
                return redirect('admin_log_in') 
        else :
            messages.error( request, 'Bad credentials')
        
    return render(request, 'admin_login/admin_log_in.html')


@never_cache
@login_required(login_url='admin_log_in')
def admin_logout(request) :
    if 'username' in request.session:
        del request.session['username'] 
    logout(request)
    messages.success(request, 'You are logged out !')
    return redirect('admin_log_in')



# ------------------- User management ---------------------

@login_required(login_url='admin_log_in')
def user_management(request) :
    all_users = User.objects.filter(is_superuser=False)
    context = {
        'all_users':all_users
    }
    return render(request, 'admin_dash/usermanage.html',context)


def search_user(request) :
    query = request.GET.get('query')
    users = User.objects.filter(username__icontains=query)
    return render(request, 'admin_dash/search_user.html',{'users':users})


@login_required(login_url='admin_log_in')
def block_unblock_user(request, user_id):
    user = User.objects.get(id=user_id)
    user.is_active = not user.is_active  
    user.save()
    if user.is_active:
        messages.success(request, f"User '{user.username}' is now available.")
    else:
        messages.warning(request, f"User '{user.username}' is now blocked.")
    return redirect('user_management')
   



#-------------------- Category Management -----------------

@login_required(login_url='admin_log_in')
def category_management(request) :
    all_category = Category.objects.all().order_by('-id')
    context = {
        'all_category':all_category
    }
    return render(request, 'admin_dash/category_manage.html',context)   



@login_required(login_url='admin_log_in')
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            description = form.cleaned_data['description']
            
            if Category.objects.filter(name=name).exists():
                form.add_error('name', 'Category with this name already exists')

            if name.isdigit():
                form.add_error('name', 'Enter a valid name')

            if description.isdigit():
                form.add_error('description', 'Enter a valid description')

            if not form.errors:
                form.save()
                messages.success(request, "Category added successfully ")
                return redirect(category_management)
                   
    else:
        form = CategoryForm()

    return render(request, 'admin_dash/add_category.html', {'form': form})



@login_required(login_url='admin_log_in')
def category_delete(request, category_id) :
    category = get_object_or_404(Category, id=category_id)
    category.is_available = not category.is_available
    category.save()
    if category.is_available :
      messages.success(request, 'Category is blocked')
      return redirect(category_management)
    else :
      messages.info(request, 'Category is unblocked')
      return redirect(category_management)
  


@login_required(login_url='admin_log_in')
def edit_category(request,category_id) :
    
    category = get_object_or_404(Category, id=category_id)
    form = CategoryForm(instance=category)
    return render(request, 'admin_dash/edit_category.html',{'form':form,'category': category})



@login_required(login_url='admin_log_in')
def update_category(request,category_id):
    if request.method == 'POST' :
        category = get_object_or_404(Category,id=category_id)
        form = CategoryForm(request.POST,instance=category)
        if form.is_valid() :
            name = form.cleaned_data['name']
            description = form.cleaned_data['description']
            if Category.objects.filter(name=name).exclude(id=category_id).exists() :
                form.add_error('name', 'Category with this name already exists !')
            if name.isdigit() :
                form.add_error('name', "Enter a valid name")
            if description.isdigit() :
                form.add_error('description', "Enter a valid description")
            if not form.errors :    
                form.save()
                messages.success(request, 'Category updated successfully')
                return redirect('category_management')
    else :
        form = CategoryForm(instance=category)   
        
    return render(request, 'admin_dash/edit_category.html',{'form':form,'category': category})




# ----------------------  Brand Management ------------------

@login_required(login_url='admin_log_in')
def brand_management(request) :
    all_brands = Brand.objects.all().order_by('-id')
    context = {
        'all_brands':all_brands
    }
    return render(request, 'admin_dash/brand_management.html',context)


@login_required(login_url='admin_log_in')
def add_brand(request) :
    if request.method == 'POST' :
        brand_name = request.POST.get('brand_name')
        if brand_name.strip() == '' :
            messages.warning(request, 'Field cannot be empty!')
            return redirect('add_brand')
        if Brand.objects.filter(name=brand_name).exists() :
            messages.warning(request, 'This Brand already exists!')
            return redirect('add_brand')
        if brand_name.isdigit() :
            messages.warning(request, 'Enter a valid Brand name')
            return redirect('add_brand')
        else :
            brand  = Brand(name=brand_name)
            brand.save()
            messages.success(request, 'Brand successfully added ')
            return redirect('brand_management')
    return render(request, 'admin_dash/add_brand.html')


@login_required(login_url='admin_log_in')
def edit_brand(request, brand_id) :
    brand = get_object_or_404(Brand, id=brand_id)
    context = {
        'brand':brand
       }
    return render(request, 'admin_dash/edit_brand.html',context) 


@login_required(login_url='admin_log_in')
def update_brand(request, brand_id) :
    if request.method == 'POST' :
        brand_name = request.POST.get('brand_name')
        if brand_name.strip() == '' :
            messages.error(request, 'Field cannot be empty!')
            return redirect('edit_brand', brand_id=brand_id)
        existing_brand = Brand.objects.filter(name=brand_name).exclude(id=brand_id)
        if existing_brand.exists() :
            messages.error(request, 'This Brand already exists !')
            return redirect('edit_brand', brand_id=brand_id)
        if brand_name.isdigit() :
            messages.error(request, 'Enter a valid Brand name')
            return redirect('edit_brand', brand_id=brand_id)

        else :

            new_brand = get_object_or_404(Brand, id=brand_id)
            new_brand.name = brand_name
            new_brand.save()
            messages.success(request, 'Brand name updated !')
            return redirect('brand_management')

    return render(request, 'admin_dash/edit_brand.html')



@login_required(login_url='admin_log_in')
def delete_brand(request,brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    brand.is_block = not brand.is_block
    brand.save()
    if brand.is_block :
        messages.warning(request, " Barnd is blocked ")
        return redirect(brand_management)
        
    else :
        messages.success(request, "Brand is available")
        return redirect(brand_management)
    


# ------------------- Product Management --------------------

@login_required(login_url='admin_log_in')
def product_management(request) :
    all_products = Product.objects.all().order_by('-id')
    context = { 'all_products':all_products}
    return render(request, 'admin_dash/product_management.html',context)


@login_required(login_url='admin_log_in')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)  
        if form.is_valid():
            name = form.cleaned_data['name']
            price = form.cleaned_data['price']
            
            if Product.objects.filter(name=name).exists() :
                form.add_error('name', 'Product with this name already exists.')
            if name.isdigit():
                form.add_error('name', 'Enter a valid product name.')
            
            try:
                float(price)
                if price < 0 :
                    form.add_error('price', 'Enter a positive number')
            except ValueError:
                form.add_error('price', 'Price must be a valid number.')

            if not form.errors:
                form.save()
                messages.success(request, "New product added successfully.")
                return redirect('product_management')

    else:
        form = ProductForm()  

    all_categories = Category.objects.all()
    brands = Brand.objects.all()
    offers = Offer.objects.filter(is_valid=True)
    context = {
        'all_categories': all_categories,
        'brands': brands,
        'form': form, 
        'offers': offers,
    }

    return render(request, 'admin_dash/add_product.html', context) 




@login_required(login_url='admin_log_in')
def edit_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    form = ProductForm(instance=product)
    all_categories = Category.objects.all()
    brands = Brand.objects.all()
    offers = Offer.objects.filter(is_valid=True)
    

    context = {
        'form': form,
        'product': product,
        'all_categories': all_categories,
        'brands': brands,
        'offers': offers
    }

    return render(request, 'admin_dash/edit_product.html', context)



@login_required(login_url='admin_log_in')
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            name = form.cleaned_data['name']
            if Product.objects.filter(name=name).exclude(id=product_id).exists() :
                form.add_error('name', 'Product With this name already exists !')
            if name.isdigit():
                form.add_error('name', 'Enter a valid product name.') 
            price = form.cleaned_data['price']    
            try :
                float(price) 
                if price < 0 :
                    form.add_error('price', 'Enter a Positive price')  
            except ValueError :
                form.add_error('price', 'Enter a valid number') 
             
            if not form.errors:
                form.save()            
                messages.success(request, 'Product updated successfully.')
                return redirect('product_management')
        else:
            messages.error(request, 'Form is not valid. Please check the errors below.')
    else:
        form = ProductForm(instance=product)

    return render(request, 'admin_dash/edit_product.html', {'form': form, 'product': product})




@login_required(login_url='admin_log_in')
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_available = not product.is_available  
    product.save()
    if product.is_available :
        messages.success(request, 'Product is available')
        return redirect('product_management')
    else :
        messages.warning(request, 'product is blocked')
        return redirect('product_management')


#  ------------------- Product variants --------------------

@login_required(login_url='admin_log_in')
def show_variants(request, product_id):
    products = Product.objects.filter(id=product_id)
    product_id= product_id
    image = Images.objects.filter(product=product_id)
    variants = Variants.objects.filter(product=product_id)
   
    return render(request, 'admin_dash/variants_product.html', {'products': products,'product_id':product_id,'image':image,'variants':variants})


# ------------------- Upload product image with fixed size --------------------

@login_required(login_url='admin_log_in')
def add_image_product(request, product_id):
    product = Product.objects.get(id=product_id)

    if request.method == 'POST':
        form = ImageForm(request.POST, request.FILES)
        if form.is_valid():
            # Open the uploaded image
            uploaded_image = Image.open(form.cleaned_data['image'])

            # Resize the image
            resized_image = uploaded_image.resize((600, 700), Image.BICUBIC)

            # Convert the image to RGB (uncomment the line below if needed)
            resized_image = resized_image.convert('RGB')

            # Create an in-memory buffer to store the resized image
            buffer = io.BytesIO()

            # Save the resized image to the buffer
            resized_image.save(buffer, format='JPEG')  # You can change the format if needed

            # Create a new Image instance and save the resized image to the 'image' field
            image = form.save(commit=False)
            image.product = product

            # Save the resized image to the 'image' field
            image.image.save('resize.jpg', buffer, save=False)

            # Save the Image instance
            image.save()

            messages.success(request, 'Product Image added successfully')
            return redirect('show_variants', product_id=product_id)

    else:
        form = ImageForm()

    return render(request, 'admin_dash/add_image_product.html', {'form': form, 'product': product})



@login_required(login_url='admin_log_in')
def delete_product_image(request,img_id) :
    image = Images.objects.get(id=img_id)
    image.delete()
    messages.info(request, 'Product Image Removed')
    product_id = image.product.id
    return redirect(reverse('show_variants', args=[product_id]))


#--------------------- Add product variants -------------------
@login_required(login_url='admin_log_in')
def add_size_and_quantity(request, product_id) :
    if request.method == 'POST' :
        size = request.POST.get('size')
        quantity = request.POST.get('quantity')
        product = Product.objects.get(id=product_id)
        if not size.isdigit() or int(size) < 0 or int(size) > 16 :
            messages.warning(request, 'Enter a valid size')
            return redirect('add_size_and_quantity', product_id=product_id)
        
        if not quantity.isdigit() or int(quantity) < 0 or int(size) > 500 :
            messages.warning(request, 'Enter a valid quantity')
            return redirect('add_size_and_quantity', product_id=product_id)

        if Variants.objects.filter(product=product, size=size).exists():
            messages.warning(request, f'A variant with size {size} already exists for this product.')
            return redirect('add_size_and_quantity', product_id=product_id)
        
        
        variant = Variants.objects.create(product=product,size=size,quantity=quantity)
        variant.save()
        messages.success(request, 'Product size & quantity updated')
        return redirect('show_variants',product_id=product_id)
    return render(request, 'admin_dash/add_size_quantity.html')



@login_required(login_url='admin_log_in')
def delete_product_size(request, variant_id) :
    variant = Variants.objects.get(id=variant_id)
    variant.delete()
    messages.info(request, 'Product size & quantity removed')
    product_id = variant.product.id
    return redirect(reverse('show_variants', args=[product_id]))



# --------------- Orders Management ----------------------------

@login_required(login_url='admin_log_in')
def all_orders(request) :
    all_orders = Order.objects.all()
    context = {'all_orders':all_orders}
    return render(request, 'admin_dash/all_orders.html',context)


@login_required(login_url='admin_log_in')
def view_single_order(request,ord_id):
    order = Order.objects.filter(tracking_no=ord_id).first()
    orderitems = OrderItem.objects.filter(order=order)
    context={
        'order':order,
        'orderitems':orderitems,
    }
    return render(request, 'admin_dash/view_single_order.html',context)



@login_required(login_url='admin_log_in')
def edit_order_status(request,ord_id):
    order = Order.objects.filter(tracking_no=ord_id).first()
    context = {'order':order}
    return render(request, 'admin_dash/edit_order_status.html',context)


@login_required(login_url='admin_log_in')
def update_order_status(request,ord_id) :
    order_updated = False 
    if request.method == 'POST' :
        new_status = request.POST.get('status')

        order = Order.objects.filter(tracking_no=ord_id).first()
        order.status = new_status
        order.save()
        messages.success(request, 'Order status updated')
        order_updated = True 
        return redirect('all_orders')
    
    return render(request, 'admin_dash/edit_order_status.html')


@login_required(login_url='admin_log_in')
def delete_order_admin(request,ord_id) :
    order_item = Order.objects.filter(tracking_no=ord_id).first()
    user_wallet, created = Wallet.objects.get_or_create(user=request.user, defaults={'wallet': 0})
    if user_wallet is None:
        raise Exception("User wallet not found or could not be created.")

    order_items = OrderItem.objects.filter(order=order_item)

    for item in order_items:
        product = item.product
        variant = Variants.objects.filter(product=product).first()
        if variant:
            variant.quantity += item.quantity
            variant.save()

    if order_item.payment_mode == 'paid by razorpay' or order_item.payment_mode == 'paid by wallet':
        if user_wallet.wallet is None:
            user_wallet.wallet = 0  # Set wallet to 0 if it is None
        user_wallet.wallet += order_item.total_price
        user_wallet.save()
        
    order_item.status = 'Cancel'    
    order_item.save()
    messages.success(request, 'Order successfully canceled.')
    print('order delete ')
    return redirect('all_orders')



# -------------------- Coupon Management ----------------

@login_required(login_url='admin_log_in')
def view_coupons(request) :
    # all_coupons = Coupon.objects.filter(is_expired=False)
    all_coupons = Coupon.objects.all().order_by('-id')
    context={'all_coupons':all_coupons}
    return render(request, 'admin_dash/coupon_management.html',context)


@login_required(login_url='admin_log_in')
def add_coupon(request) :
    if request.method=='POST' :
        code = request.POST.get('coupon')
        min_amount = request.POST.get('minimum_amount')
        dis_amount = request.POST.get('discount_amount')
        if code.strip()=='' or min_amount.strip()=='' or dis_amount.strip()=='' :
            messages.warning(request, 'Fields cannot be empty!')
            return redirect('add_coupon')
        if code.isdigit() :
            messages.error(request, 'Coupon code can not only contain numbers')
            return redirect('add_coupon')
        if not min_amount.isdigit() or int(min_amount) < 0  :
            messages.error(request, 'Ente a valid Minimum Amount')
            return redirect('add_coupon')
        if not dis_amount.isdigit() or int(dis_amount)<0  :
            messages.error(request, 'Ente a valid Discount Amount')
            return redirect('add_coupon')
        if int(dis_amount) > int(min_amount) :
            messages.error(request, 'Discount amount should be lessthan  Minimum Amount')
            return redirect('add_coupon')

        if Coupon.objects.filter(coupon_code=code).exists() :
            messages.warning(request, 'Coupon already exist!')
            return redirect('add_coupon')
        coupon = Coupon.objects.create(
            coupon_code = code,
            minimum_amount = min_amount,
            discound_amount = dis_amount,
            )
        coupon.save()
        messages.success(request, 'Coupon successfully added')
        return redirect('view_coupons')
    return render(request, 'admin_dash/add_coupon.html')


@login_required(login_url='admin_log_in')
def delete_coupon(request,c_id) :
    coupon = Coupon.objects.get(id=c_id) 
    if coupon.is_expired==False :
        coupon.is_expired=True
        coupon.save()
        messages.warning(request, 'Coupon is blocked')
        return redirect('view_coupons')
    else :
        coupon.is_expired=False
        coupon.save()
        messages.success(request, 'Coupon is Unblocked')
        return redirect('view_coupons')
    

# ------------------- Offer Management ------------------

def view_offers(request) :
    offers = Offer.objects.all().order_by('-start_date', '-id')
    return render(request, 'admin_dash/offer_management.html',{'offers':offers})

def add_offer(request):
    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            end_date = form.cleaned_data['end_date']
            try:
                end_date.strftime('%Y-%m-%d')
            except ValueError:
                form.add_error('end_date', 'Invalid date format. Please use YYYY-MM-DD.')

            now = timezone.now()
            if end_date <= now:
                form.add_error('end_date', 'End date must be greater than the current date and time.')

            discount_percentage = form.cleaned_data['discount_percentage']
            try:
                float(discount_percentage)
                if discount_percentage < 0 :
                    form.add_error('discount_percentage', 'Enter a Positive number')
                if discount_percentage > 75 :
                    form.add_error('discount_percentage', 'Only 75% maximum discount percentage allowed!') 

            except ValueError:
                form.add_error('discount_percentage', 'Discount amount must be a valid number.')

            if not form.errors:
                form.save()
                messages.success(request, "Offer added successfully.")
                return redirect('view_offers')

    else:
        form = OfferForm()

    context = {'form': form}
    return render(request, 'admin_dash/add_offer.html', context)



def delete_offer(request, off_id):
    offer = get_object_or_404(Offer, id=off_id)
    offer.is_block = not offer.is_block
    offer.save()

    if offer.is_block:
        messages.success(request, "Offer is Blocked")
        return redirect('view_offers')  
    else:
        messages.success(request, "Offer is Unblocked")
        return redirect('view_offers')  
    


# --------------- Category offer ( apply offer for category )----------------

@login_required(login_url='admin_log_in')
def view_category_offers(request) :
    categories = Category.objects.filter(is_available=True).order_by('-id')
    return render(request, 'admin_dash/category_offers.html',{'categories':categories})


@login_required(login_url='admin_log_in')
def offers_for_category(request,c_id) :
    category = get_object_or_404(Category, id=c_id)
    form = CategoryOfferForm(instance=category)
    return render(request, 'admin_dash/apply_offer_for_category.html',{'form':form,'category':category}) 


@login_required(login_url='admin_log_in')
def update_category_offer(request,c_id) :
    category = get_object_or_404(Category, id=c_id)
    if request.method == 'POST' :
        form = CategoryOfferForm(request.POST,instance=category)
        if form.is_valid() :
            form.save()
            
            products_in_category = Product.objects.filter(categories=category)
            for product in products_in_category :
                product.offer = category.offer
                product.save()
            messages.success(request, 'Offer applied for category')
            return redirect(view_category_offers)
    else :
        form = CategoryForm(instance=category)

    return render(request, 'admin_dash/apply_offer_for_category.html') 


@login_required(login_url='admin_log_in')
def remove_category_offer(request,c_id) :
    category = get_object_or_404(Category,id=c_id)
    category.offer = None
    category.save()
    products_with_offer = Product.objects.filter(categories=category)
    for product in products_with_offer :
        product.offer = None
        product.save()
    messages.success(request, 'Category offer removed !')
    return redirect(view_category_offers)
   


# ---------------- Product Offer (apply offer for product ) ------------------

@login_required(login_url='admin_log_in')
def veiw_product_offers(request) :
    products = Product.objects.filter(is_available=True).order_by('-id')
    return render(request, 'admin_dash/product_offers.html',{'products':products})

@login_required(login_url='admin_log_in')
def offers_for_product(request,p_id) :
    product = get_object_or_404(Product, id=p_id)
    form = ProductOfferForm(instance=product)
    return render(request, 'admin_dash/apply_offer_for_product.html',{'form':form,'product':product})

@login_required(login_url='admin_log_in')
def update_product_offer(request,p_id) :
    product = get_object_or_404(Product,id=p_id) 
    if request.method == 'POST' :
        form = ProductOfferForm(request.POST,instance=product)
        if form.is_valid() :
            form.save()
            messages.success(request, 'Offer applied for Product')
            return redirect(veiw_product_offers)
    else :
        form = ProductOfferForm(instance=product)
    return render(request, 'admin_dash/apply_offer_for_product.html')


@login_required(login_url='admin_log_in')
def remove_product_offer(request,p_id) :
    product = get_object_or_404(Product,id=p_id)
    product.offer = None
    product.save()
    messages.success(request, 'Product offer removed !')
    return redirect(veiw_product_offers)



# ----------------------- Banner Management ----------------

@login_required(login_url='admin_log_in')
def banner_management(request):
    all_banner = Banner.objects.exclude(banner__isnull=True)
    context = {
        'all_banner': all_banner,
    }
    return render(request, 'admin_dash/banner_management.html', context)


@login_required(login_url='admin_log_in')
def add_banner_image(request) :
    if request.method == 'POST' :
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid() :
            title      = form.cleaned_data['title']
            subtitle_1 = form.cleaned_data['subtitle_1']
            subtitle_2 = form.cleaned_data['subtitle_2']

            if title.isdigit() :
                form.add_error('title', 'Ente a valid Banner title ')

            if subtitle_2.isdigit() :
                form.add_error('subtitle_1', "Enter a valid subtitle ")

            if subtitle_1.isdigit() :
                form.add_error('subtitle_2', "Enter a valid subtitle ")
            if subtitle_1 == subtitle_2 :
                form.add_error('subtitle_2', "Subtitle 1 and Subtitle 2 must be different.")

            if not form.errors :        
                form.save()
                messages.success(request, "Banner successfully Added")
                return redirect('banner_management')
    else :
        form = BannerForm()  
    return render(request, 'admin_dash/add_banner.html',{'form':form})


@login_required(login_url='admin_log_in')
def delete_banner(request,b_id) :
    banner = get_object_or_404(Banner, id=b_id)
    if banner.is_available == True :
        banner.is_available = False
        banner.save()
        messages.success(request, 'Banner blocked !')
        return redirect('banner_management')
    else :
        banner.is_available = True
        banner.save()
        messages.success(request, 'Banner Unblocked ')
        return redirect('banner_management')



#-------------------- Dash board data ----------------------

@login_required(login_url='admin_log_in')
def dash_board(request) :
    total_products   = Product.objects.filter(is_available=True).count()
    total_revenue    = Order.objects.filter(status='Deliverd').aggregate(Sum('total_price'))['total_price__sum'] or 0
    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = Order.objects.filter(status='Deliverd', created_at__gte=start_of_month).aggregate(Sum('total_price'))['total_price__sum'] or 0

    total_sales      = Order.objects.filter(status='Deliverd').count()
    total_customers  = User.objects.filter(is_active=True,is_superuser=False).count()
    total_orders = (
        OrderItem.objects.filter(order__status='Deliverd')
        .aggregate(count=Count('id'))
    )['count'] or 0

    cod_count = Order.objects.filter(status='Deliverd', payment_mode='COD').count()
    razorpay_count = Order.objects.filter(status='Deliverd', payment_mode='paid by razorpay').count()
    wallet_count = Order.objects.filter(status='Deliverd', payment_mode='paid by wallet').count()
    
    order_item_counts_by_month = (
        OrderItem.objects.filter(order__status='Deliverd')
        .annotate(month=TruncMonth('order__created_at'))
        .values('month')
        .annotate(count=Count('id'))
    )

    # Create a dictionary with month as key and count as value
    order_item_counts_dict = {entry['month'].strftime('%Y-%m'): entry['count'] for entry in order_item_counts_by_month}

    # Generate a list of all 12 months
    all_months = [(start_of_month - timedelta(days=30 * i)).strftime('%Y-%m') for i in range(11, -1, -1)]

    # Fill in counts for each month, defaulting to zero if no data for that month
    order_item_counts_data = [order_item_counts_dict.get(month, 0) for month in all_months]

   

    context = {
        'total_products'  :total_products,
        'total_customers' :total_customers,
        'total_revenue'   : total_revenue,
        'monthly_revenue' : monthly_revenue,
        'total_sales'     : total_sales,
        'total_orders'    : total_orders,
        'cod_count'       : cod_count,
        'razorpay_count'  : razorpay_count,
        'wallet_count'    : wallet_count,
        'order_item_chart_labels': all_months,
        'order_item_chart_data': order_item_counts_data,
       
       
    }
    return render(request, 'admin_dash/admin_dash.html',context)



@login_required(login_url='admin_log_in')
def view_sales_reports(request) :
    time_range = request.GET.get('time_range')

    if not time_range:
        time_range = 'all'

    if time_range == 'day':
        # start_date = timezone.now() - timedelta(days=1)
        start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    elif time_range == 'week':
        start_date = timezone.now() - timedelta(weeks=1)
    elif time_range == 'month':
        start_date = timezone.now() - timedelta(days=30)
    elif time_range == 'year':
        start_date = timezone.now() - timedelta(days=365)
    elif time_range == 'all':
        start_date = timezone.now() - timedelta(days=365) 
    else:
        # Handle invalid time_range values or implement additional options as needed
        start_date = timezone.now()

    # orders = Order.objects.filter(status='Deliverd').order_by('-id')
    orders = Order.objects.filter(status='Deliverd', created_at__gte=start_date).order_by('-id')
    return render(request, 'admin_dash/view_sales_reports.html', {'orders': orders, 'selected_time_range': time_range})



# ----------------- Generate sales report (PDF) -------------------

@login_required(login_url='admin_log_in')
def download_pdf(request):
    time_range = request.GET.get('time_range')

    if not time_range:
        time_range = 'all'

    if time_range == 'day':
        # start_date = timezone.now() - timedelta(days=1)
        start_date = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)

    elif time_range == 'week':
        start_date = timezone.now() - timedelta(weeks=1)
    elif time_range == 'month':
        start_date = timezone.now() - timedelta(days=30)
    elif time_range == 'year':
        start_date = timezone.now() - timedelta(days=365)
    elif time_range == 'all':
        start_date = timezone.now() - timedelta(days=365)  # Or adjust the duration as needed for all reports
    else:
        # Handle invalid time_range values or implement additional options as needed
        start_date = timezone.now()
    orders = Order.objects.filter(status='Deliverd', created_at__gte=start_date).order_by('-id')
    total_sale_amount = 0
    for order in orders :
        total_sale_amount += order.total_price

    context = {
        'orders': orders,
        'total_sale_amount': total_sale_amount,
        # 'selected_time_range': request.GET.get('time_range', 'all'),
    }

    pdf = render_to_pdf('pdfs/salesreport.html', context)

    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'filename="sales_report.pdf"'
        return response

    return HttpResponse("Error generating PDF", status=500)




def get_sales_data(request, period):
    if period == 'week':
        start_date = timezone.now().date() - timezone.timedelta(days=6)
        order_items = OrderItem.objects.filter(order__created_at__gte=start_date)
        data = (
            order_items.annotate(day=TruncDay('order__created_at'))
            .values('day')
            .annotate(total=Sum(F('quantity') * F('price')))
            .order_by('day')
        )
        labels = [item['day'].strftime('%A') for item in data]
    elif period == 'month':
        start_date = timezone.now().date() - timezone.timedelta(days=30)
        order_items = OrderItem.objects.filter(order__created_at__gte=start_date)
        data = (
            order_items.annotate(day=TruncDay('order__created_at'))
            .values('day')
            .annotate(total=Sum(F('quantity') * F('price')))
            .order_by('day')
        )
        labels = [item['day'].strftime('%Y-%m-%d') for item in data]
    elif period == 'year':
        start_date = timezone.now().date() - timezone.timedelta(days=365)
        order_items = OrderItem.objects.filter(order__created_at__gte=start_date)
        data = (
            order_items.annotate(month=TruncMonth('order__created_at'))
            .values('month')
            .annotate(total=Sum(F('quantity') * F('price')))
            .order_by('month')
        )
        labels = [f"{item['month'].strftime('%B')}" for item in data]
    else:
        return JsonResponse({'error': 'Invalid period'})

    sales_data = [item['total'] for item in data]
    return JsonResponse({'labels': labels, 'data': sales_data})

