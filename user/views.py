from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth import authenticate,login,logout
from django.core.mail import send_mail
from django.contrib import messages
# from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .forms import CreateUserForm
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
import re
from django.core.paginator import Paginator,EmptyPage, InvalidPage
from admin_dash.models import Product,Category,Brand,Variants,Banner
from django.core.exceptions import ObjectDoesNotExist
import pyotp
from datetime import datetime,timedelta
from django.http import HttpResponse


# ------------------  User Registration ------------------

@never_cache
def sign_up(request):
    if request.user.is_authenticated:
        return render(request, 'base.html')
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password1 = request.POST.get('password1', '').strip()
        password2 = request.POST.get('password2', '').strip()

        if not first_name or not last_name or not username or not email or not password1 or not password2:
            messages.error(request, "Please fill in all the required fields.")
            return redirect('sign_up')
        if not first_name.isalpha():
            messages.error(request, "First name should only contain alphabetic characters.")
            return redirect('sign_up')
        
        if not last_name.isalpha():
            messages.error(request, "First name should only contain alphabetic characters.")
            return redirect('sign_up')

        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            messages.error(request, "Please enter a valid email address.")
            return redirect('sign_up')
        
        if username.isdigit():
            messages.error(request, "Username should not only contain digits.")
            return redirect('sign_up')

        if User.objects.filter(username=username).exists():
            messages.error(request, "Username is already taken. Please choose another one.")
            return redirect('sign_up')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email address is already registered. Please use a different email.")
            return redirect('sign_up')

        if password1 != password2:
            messages.error(request, "Passwords do not match. Please enter the same password in both fields.")
            return redirect('sign_up')

        if len(password1) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return redirect('sign_up')
        
        if not any(char.isupper() for char in password1):
            messages.error(request, "Password must contain at least one uppercase letter.")
            return redirect('sign_up')
        
        if not any(char.isdigit() for char in password1):
            messages.error(request, "Password must contain at least one digit.")
            return redirect('sign_up')
            
      
        user = User.objects.create_user(username=username, email=email, password=password1, first_name=first_name, last_name=last_name)
        user.save()
        request.session['email'] = email
        request.session['password'] = password1
        send_otp(request)
        return render(request, 'user/otp.html', {'email': email})

    return render(request, 'user/sign_up.html')


@never_cache
def log_in(request):
    if request.user.is_authenticated:
        return render(request, 'base.html')
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        try:
            user = User.objects.get(email=email.lower())
             
            if not user.is_active:
                messages.error(request, 'Your account is blocked. Please contact support.')
                return render(request, 'user/log_in.html')
            
            if user.is_superuser:
                messages.error(request, 'Superusers cannot login through this page.')
                return render(request, 'user/log_in.html')
            
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, 'You have successfully logged in')
                return redirect('home')
            else:
                messages.error(request, 'Oops.. Bad credentials!')
        except ObjectDoesNotExist:
            messages.error(request, 'User with this email does not exist')
    return render(request, 'user/log_in.html')



@never_cache
def log_out(request):
    if request.user.is_authenticated:
        request.session.flush()  # Clear the entire session
        logout(request)
        messages.success(request, "You are logged out!")
    else:
        messages.warning(request, "You are not logged in.")
    return redirect('home')


# ----------------------  OTP functionality for user verification ---------------------

def send_otp(request):
    totp_secret_key = pyotp.random_base32()
    totp = pyotp.TOTP(totp_secret_key, interval=60)
    otp = totp.now()
    request.session['otp_secret_key'] = totp_secret_key  
    request.session['otp_valid_date'] = str(datetime.now() + timedelta(minutes=1))
    request.session['otp'] = otp  

    email_template = 'user/email_otp.html'
    html_message = render(request, email_template, {'otp': otp}).content.decode('utf-8')

    send_mail(
        subject="OTP for Sign Up",
        message="", 
        from_email='shamilnk0458@gmail.com',
        recipient_list=[request.session['email']],
        html_message=html_message,
        fail_silently=False
    )

    return render(request, 'user/otp.html')



def otp_verification(request):
    if request.method == 'POST':
        entered_otp = request.POST['otp']
        stored_otp = request.session.get('otp') 
        otp_secret_key = request.session.get('otp_secret_key')
        otp_valid_date = request.session.get('otp_valid_date')

        if otp_secret_key and otp_valid_date is not None:
            valid_until = datetime.fromisoformat(otp_valid_date)

            if valid_until > datetime.now():
                if entered_otp == stored_otp:
                    email = request.session['email']
                    password = request.session['password']
                    username = User.objects.get(email=email.lower()).username
                    user = authenticate(request, username=username, password=password)
                    if user is not None:
                        login(request, user)
                        return redirect('home')
                else:
                    messages.error(request, "Invalid OTP. Please enter a valid OTP.")
            else:
                messages.error(request, "OTP has expired. Please request a new OTP.")
        else:
            messages.error(request, "OTP validation failed. Please request a new OTP.")
    return render(request, 'user/otp.html')



def resend_otp(request):
   
    totp_secret_key = pyotp.random_base32()
    totp = pyotp.TOTP(totp_secret_key, interval=60)
    otp = totp.now()
    request.session['otp_secret_key'] = totp_secret_key
    request.session['otp_valid_date'] = str(datetime.now() + timedelta(minutes=1))
    request.session['otp'] = otp

    send_mail("Resent OTP for sign up", otp, 'shamilnk0458@gmail.com', [request.session['email']], fail_silently=False)
    messages.success(request, "OTP has been resent. Please check your email.")
    return render(request, 'user/otp.html')



#--------------------- Home Page ------------------

@never_cache
def home(request) :
    all_products = Product.objects.filter(is_available =True).order_by('-id')[:8]
    # banner = Banner.objects.filter(is_available=True).order_by('-id').first()
    # banner_2 = Banner.objects.filter(is_available=True).order_by('-id')[1]
    banners = list(Banner.objects.filter(is_available=True).order_by('-id')[:2])
    banner = banners[0] if len(banners) > 0 else None
    banner_2 = banners[1] if len(banners) > 1 else None

    return render(request, 'base.html',{'all_products':all_products,'banner':banner,'banner_2':banner_2})



# --------------------- View single product details ---------------

@never_cache
def show_single_product(request,product_id) :
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(categories=product.categories).exclude(id=product_id)[:4]

    context = {
        'product':product,
        'related_products':related_products,
    }
    return render(request, 'single_product.html',context)



# ------------------------ Store Page (explore all products) -------------------

def store(request):
    cate_id = request.GET.get('categories')
    brand_id = request.GET.get('brand') 
   
    products = Product.objects.filter(is_available=True)
    categories = Category.objects.all()
    brands = Brand.objects.all()
    category = None 
    brand = None
    

    if brand_id and brand_id != 'None':
        products = products.filter(brand__id=brand_id)
        brand = products

    if cate_id and cate_id != 'None':
        category = get_object_or_404(Category, id=cate_id)
        products = Product.objects.filter(categories=category)

    paginator = Paginator(products, 4)
    page_number = request.GET.get('page')
    all_products = paginator.get_page(page_number)

    context = {
        'categories': categories,
        'all_products': all_products,
        'brands': brands,
        'brand_id': brand_id,
        'cate_id': cate_id,
        'category': category, 
        'brand': brand,
    }

    return render(request, 'store.html', context)



#-------------------- Search products ----------------
def search_products(request):
    query = request.GET.get('query')
    products = Product.objects.filter(is_available=True)

    if query:  
        products = products.filter(name__icontains=query)

    paginator = Paginator(products, 4)
    page_number = request.GET.get('page')

    try:
        all_products = paginator.page(page_number)
    except (EmptyPage, InvalidPage):
        all_products = paginator.page(1)

    context = {'all_products': all_products}
    return render(request, 'search_products.html', context)
