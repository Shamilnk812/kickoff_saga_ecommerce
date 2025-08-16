from django.shortcuts import get_object_or_404, render,redirect
from django.contrib.auth import authenticate,login,logout
from django.core.mail import send_mail
from django.contrib import messages
from django.conf import settings
from django.contrib.auth.models import User
from .models import *
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import login_required
import re
from django.core.paginator import Paginator
from admin_dash.models import Product,Category,Brand,Variants,Banner
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime,timedelta
from django.http import HttpResponse
from django.db.models import Q
from .utils import *
from .forms import *

# ------------------  User Registration ------------------
def sign_up(request):
    if request.user.is_authenticated:
        return render(request, 'base.html')

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password1"])  
            user.save()
            UserProfile.objects.create(user=user, is_verified=False)

            request.session['email'] = user.email
            request.session['password'] = form.cleaned_data["password1"]
            send_otp(request)

            return render(request, 'user/otp.html', {'email': user.email})
        
    else:
        form = UserRegistrationForm()

    return render(request, 'user/sign_up.html', {'form': form})



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
                return redirect('log_in')
            
            if user.is_superuser:
                messages.error(request, 'Admin cannot login through this page.')
                return redirect('log_in')
            
            user = authenticate(request, username=user.username, password=password)
            if user is not None:
                if UserProfile.objects.filter(user=user, is_verified=True):
                    login(request, user)
                    messages.success(request, 'You have successfully logged in')
                    return redirect('home')
                else:
                    messages.error(request, 'You account is not verified')
                    return redirect('log_in')
            else:
                messages.error(request, 'Oops.. Bad credentials!')
        except ObjectDoesNotExist:
            messages.error(request, 'User with this email does not exist')
    return render(request, 'user/log_in.html')



@never_cache
def log_out(request):
    if request.user.is_authenticated:
        request.session.flush() 
        logout(request)
        messages.success(request, "You are logged out!")
    else:
        messages.warning(request, "You are not logged in.")
    return redirect('home')




# ------------------- OTP functionality for user verification -----------------
def send_otp(request):
    otp = generate_otp(request)
    email_template = 'user/email_otp.html'
    html_message = render(request, email_template, {'otp': otp}).content.decode('utf-8')

    send_mail(
        subject="OTP for Sign Up",
        message="", 
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[request.session['email']],
        html_message=html_message,
        fail_silently=False
    )

    return render(request, 'user/otp.html')



def otp_verification(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otp', '').strip()
        saved_otp = request.session.get('otp')
        otp_valid_date = request.session.get('otp_valid_date')
       
        if not saved_otp or not otp_valid_date:
            messages.error(request, "OTP validation failed. Please request a new OTP.")
        elif datetime.now() > datetime.fromisoformat(otp_valid_date):
            messages.error(request, "OTP has expired. Please request a new OTP.")
        elif entered_otp != saved_otp:
            messages.error(request, "Invalid OTP. Please enter a valid OTP.")
        else:
            email = request.session.get('email')
            password = request.session.get('password')
            try:
                username = User.objects.get(email=email.lower()).username
            except User.DoesNotExist:
                messages.error(request, "User not found.")
                return render(request, 'user/otp.html')

            user = authenticate(request, username=username, password=password)
            if user:
                user_profile= UserProfile.objects.get(user=user)
                user_profile.is_verified = True
                user_profile.save()
                login(request, user)
                messages.success(request, 'You have successfully logged in')
                return redirect('home')
            else:
                messages.error(request, "Authentication failed. Please try again later")

    return render(request, 'user/otp.html')



def resend_otp(request):
   
    otp = generate_otp(request)
    email_template = 'user/email_otp.html'
    html_message = render(request, email_template, {'otp': otp}).content.decode('utf-8')

    send_mail(
        subject="OTP for Sign Up",
        message='',
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[request.session['email']],
        html_message=html_message,
        fail_silently=False
    )
    messages.success(request, "OTP has been resent. Please check your email.")
    return render(request, 'user/otp.html')



#------------- Home Page -------

def home(request) :
    all_products = Product.objects.select_related('brand', 'categories').filter(
        is_available=True,
        categories__is_available=True,
        brand__is_available=True,
        status='published'
    ).order_by('-id')[:8]

    banners = Banner.objects.filter(is_available=True).order_by('-id')
    return render(request, 'base.html',{'all_products':all_products, 'banners': banners})



# ------- View single product details ---------

def show_single_product(request,product_id) :
    product = get_object_or_404(Product, id=product_id)
    related_products = Product.objects.filter(categories=product.categories).exclude(id=product_id)[:4]

    context = {
        'product':product,
        'related_products':related_products,
    }
    return render(request, 'single_product.html',context)



# -------- Store Page (explore all products) --------
def store(request):
    cate_id = request.GET.get('categories')
    brand_id = request.GET.get('brand') 
    query = request.GET.get('query')
   
    products = Product.objects.filter(
        is_available=True,
        categories__is_available=True,
        brand__is_available=True,
        status='published'
        )
    
    if query:
        products = products.filter(
           Q(name__icontains=query) | 
           Q(brand__name__icontains=query)|
           Q(categories__name__icontains=query) 
        )
    
    categories = Category.objects.filter(is_available=True)
    brands = Brand.objects.filter(is_available=True)
    category = None 
    brand = None
    

    if brand_id and brand_id != 'None':
        products = products.filter(brand__id=brand_id)
        brand = products

    if cate_id and cate_id != 'None':
        category = get_object_or_404(Category, id=cate_id)
        products = products.filter(categories=category)

    paginator = Paginator(products, 8)
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
        'query': query,
    }

    return render(request, 'store.html', context)
