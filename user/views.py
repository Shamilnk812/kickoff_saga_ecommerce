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
import logging
from django.core.paginator import Paginator
from admin_dash.models import Product,Category,Brand,Variants,Banner
from django.core.exceptions import ObjectDoesNotExist
from datetime import datetime,timedelta
from django.http import HttpResponse
from django.db.models import Q , Case, When, F, DecimalField, Value
from .utils import *
from .forms import *
logger = logging.getLogger(__name__)




# ----------- User Registration -------------
def sign_up(request):
    try:
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
                try:
                    send_otp(request)

                except Exception as otp_error:
                    logger.error(f"Failed to send OTP for {user.email}: {otp_error}")
                    messages.error(request, "Could not send OTP. Please try again later.")
                    return render(request, 'user/sign_up.html', {'form': form})

                return render(request, 'user/otp.html', {'email': user.email})
            
        else:
            form = UserRegistrationForm()
        return render(request, 'user/sign_up.html', {'form': form})
    
    except Exception as e:
        logger.error(f"Unexpected error in sign_up view: {e}")
        messages.error(request, "Something went wrong. Please try again later.")
        return render(request, 'user/sign_up.html', {'form': UserRegistrationForm()})



def log_in(request):
    try:
        if request.user.is_authenticated:
            return render(request, 'base.html')
        if request.method == 'POST':
            email = request.POST.get('email')
            password = request.POST.get('password')
            try:
                user = User.objects.get(email=email.lower())
                
                if not user.is_active:
                    messages.error(request, 'Your account is blocked. Please contact support.')
                    return redirect('login')
                
                if user.is_superuser:
                    messages.error(request, 'Admin cannot login through this page.')
                    return redirect('login')
                
                user = authenticate(request, username=user.username, password=password)
                if user is not None:
                    if UserProfile.objects.filter(user=user, is_verified=True):
                        login(request, user)
                        messages.success(request, 'You have successfully logged in')
                        return redirect('home')
                    else:
                        messages.error(request, 'You account is not verified')
                        return redirect('login')
                else:
                    messages.error(request, 'Oops.. Bad credentials!')
            except ObjectDoesNotExist:
                messages.error(request, 'User with this email does not exist')
        return render(request, 'user/log_in.html')
    
    except Exception as e:
        logger.error(f"Unexpected error in log_in view: {e}", exc_info=True)
        messages.error(request, 'Something went wrong. Please try again later.')
        return render(request, 'user/log_in.html')



@never_cache
def log_out(request):
    try:
        if request.user.is_authenticated:
            request.session.flush() 
            logout(request)
            messages.success(request, "You are logged out!")
        else:
            messages.warning(request, "You are not logged in.")
        return redirect('home')

    except Exception as e:
        logger.error(f"Unexpected error in log_out view: {e}", exc_info=True)
        messages.error(request, "Something went wrong. Please try again.")
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
    try:
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
    
    except Exception as e:
        logger.error(f"Unexpected error in otp_verification view: {e}")
        messages.error(request, "Something went wrong. Please try again later.")
        return render(request, 'user/otp.html')



def resend_otp(request):
    try:
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
    
    except Exception as e:
        logger.error(f"Unexpected error in resend_otp view: {e}", exc_info=True)
        messages.error(request, "Something went wrong. Please try again later.")
        return render(request, 'user/otp.html')


#----------- Home Page -------
def home(request) :
    try:
        all_products = Product.objects.select_related('brand', 'categories').filter(
            is_available=True,
            categories__is_available=True,
            brand__is_available=True,
            status='published'
        ).order_by('-id')[:8]

        banners = Banner.objects.filter(is_available=True).order_by('-id')
        for product in all_products:
            product.sizes_list = ",".join([str(v.size) for v in product.variants_set.all()])

        return render(request, 'base.html',{'all_products':all_products, 'banners': banners})
    
    except Exception as e:
        logger.error(f"Unexpected error in home view: {e}")
        return render(request, 'show_error.html')


# ------- View single product details ---------
def show_single_product(request,product_id) :
    try:
        product = get_object_or_404(Product, id=product_id)
        related_products = Product.objects.filter(categories=product.categories).exclude(id=product_id)[:4]
        for item in related_products:
            item.sizes_list = ",".join([str(v.size) for v in item.variants_set.all()])

        context = {
            'product':product,
            'related_products':related_products,
        }
        return render(request, 'single_product.html',context)
    
    except Exception as e:
        logger.error(f"Unexpected error in show_single_product view: {e}")
        messages.error(request, "Something went wrong while loading the product. Please try again later.")
        return redirect('home')


# -------- Store Page (explore all products) --------
def store(request):
    try:
        cate_id = request.GET.get('categories')
        brand_id = request.GET.get('brand') 
        query = request.GET.get('query')
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        sortby = request.GET.get('sortby') 

        products = Product.objects.filter(
            is_available=True,
            categories__is_available=True,
            brand__is_available=True,
            status='published'
        ).annotate(
            effective_price=Case(
                When(
                    offer__isnull=False,
                    then=F("price") - (F("price") * F("offer__discount_percentage") / Value(100.0))
                ),
                default=F("price"),
                output_field=DecimalField(max_digits=10, decimal_places=2)
            )
        )

        if query:
            products = products.filter(
            Q(name__icontains=query) | 
            Q(brand__name__icontains=query) |
            Q(categories__name__icontains=query) 
            )

        categories = Category.objects.filter(is_available=True)
        brands = Brand.objects.filter(is_available=True)
        category = None 
        brand = None

        if brand_id and brand_id != 'None':
            products = products.filter(brand__id=brand_id)
            brand = get_object_or_404(Brand, id=brand_id)

        if cate_id and cate_id != 'None':
            category = get_object_or_404(Category, id=cate_id)
            products = products.filter(categories=category)

        if min_price and max_price:
            try:
                min_price = int(min_price)
                max_price = int(max_price)
            except ValueError:
                messages.error(request, "Price must be a valid number.")
                return redirect('store')

            if min_price > max_price:
                messages.error(request, "Minimum price should be less than Maximum price.")
                return redirect('store')

            if min_price < 0 or max_price < 0:
                messages.error(request, "Price values must be positive.")
                return redirect('store')
            products = products.filter(price__gte=min_price, price__lte=max_price)
        
        if sortby == "price_low_high":
            products = products.order_by("effective_price")
        elif sortby == "price_high_low":
            products = products.order_by("-effective_price")
        elif sortby == "date":
            products = products.order_by("-created_date")

        for product in products:
            product.sizes_list = ",".join([str(v.size) for v in product.variants_set.all()])

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
            'min_price': min_price,
            'max_price': max_price,
            'sortby':sortby,
        }

        return render(request, 'store.html', context)
    
    except Exception as e:
        logger.error(f"Unexpected error in store view: {e}")
        messages.error(request, "Something went wrong while loading the store.")
        return redirect('home')
