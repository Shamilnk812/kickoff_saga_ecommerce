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
from django.db.models import Sum,Count,F, Q
from django.utils import timezone
from datetime import timedelta,datetime,date
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from .helpers import render_to_pdf
from django.db.models.functions import TruncMonth,TruncDay
from PIL import Image, ImageFilter
from .constants import ORDER_STATUS_FLOW as STATUS_FLOW
from cart.utils import create_payment
# from PIL import Image
# from io import BytesIO
# from django.core.files.uploadedfile import InMemoryUploadedFile
from django.http import JsonResponse
from django.core.paginator import Paginator
from .utils import *
from decimal import Decimal, ROUND_HALF_UP






# ------------- Admin auth --------------

def admin_log_in(request) :
    if request.method == 'POST' :
        username = request.POST.get('username')
        password = request.POST.get('password')
        if username.strip()=='' or password.strip()=='':
            messages.error(request, 'Fields cannot be empty!')
            return redirect('admin-login')
        user = authenticate(username=username,password=password)
        if user is not None :
            if user.is_active :
                if user.is_superuser :
                    login(request, user)
                    return redirect('dashboard')
                else:
                    messages.error(request, 'Sorry only admin is allowed to ') 
                    return redirect('admin-login')   
            else :
                messages.warning(request, 'Your account has been blocked')   
                return redirect('admin-login') 
        else :
            messages.error( request, 'Bad credentials')
        
    return render(request, 'admin_login/admin_log_in.html')


@never_cache
@login_required(login_url='admin-login')
def admin_logout(request) :
    if 'username' in request.session:
        del request.session['username'] 
    logout(request)
    messages.success(request, 'You are logged out !')
    return redirect('admin-login')



# ------------------- User management ---------------------

@login_required(login_url='admin-login')
def user_management(request) :
    query = request.GET.get('query')

    if query:
        users = User.objects.filter(
            Q(username__icontains=query) | Q(email__icontains=query),
            is_superuser=False
            ).order_by('-id')
    else:
        users = User.objects.filter(is_superuser=False).order_by('-id')
   
    paginate_query = paginate_queryset(users, request, 8)
    
    context = {
        'all_users': paginate_query,
        'query': query,
    }
    return render(request, 'admin_dash/usermanage.html',context)

# def search_user(request) :
#     query = request.GET.get('query')
#     users = User.objects.filter(username__icontains=query)
#     return render(request, 'admin_dash/search_user.html',{'users':users})


@login_required(login_url='admin-login')
def block_user(request, user_id):
    blocking_reason = request.POST.get('blocking_reason', '').strip()

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.warning('User data doesnot exist')
        return redirect('user-management')
    
    if not blocking_reason:
            messages.warning(request, "Blocking reason is required.")
            return redirect('user-management')
    if len(blocking_reason) < 10:
            messages.warning(request, "Blocking reason must be at least 10 characters. Please enter valid reason.")
            return redirect('user-management')
    if blocking_reason.isdigit() or re.fullmatch(r'[^\w\s]+', blocking_reason):
            messages.warning(request, "Blocking reason must contain valid text, not just digits or special characters.")
            return redirect('user-management')
     
    user.is_active = False
    user.save()
    # Send account block email
    send_block_email(user.email, user.username, blocking_reason)
    messages.success(request, f'{user.username} Account is blocked successfully')
    return redirect('user-management')



@login_required(login_url='admin-login')
def unblock_user(request, user_id):
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        messages.warning('User data doesnot exist')
        return redirect('user-management')
    
    user.is_active = True
    user.save()

    # send account unblok email 
    send_account_unblock_email(user.email, user.username)

    messages.success(request, f'{user.username} Account is unblocked')
    return redirect('user-management')




#-------------------- Category Management -----------------

@login_required(login_url='admin-login')
def category_management(request) :
    query = request.GET.get('query')
    if query:     
        all_category = Category.objects.filter(name__icontains=query).order_by('-id')
    else:
        all_category = Category.objects.all().order_by('-id')

    paginate_query = paginate_queryset(all_category, request, 8)

    context = {
        'all_category':paginate_query,
        'query':query,
    }
    return render(request, 'admin_dash/category_manage.html',context)   



@login_required(login_url='admin-login')
def add_category(request):
    if request.method == 'POST':
        form = CategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Category added successfully ")
            return redirect('category-management')
    else:
        form = CategoryForm()

    return render(request, 'admin_dash/add_category.html', {'form': form})



@login_required(login_url='admin-login')
def update_category(request,category_id):
    category = get_object_or_404(Category, id=category_id)

    if request.method == 'POST' :
        form = CategoryForm(request.POST,instance=category)
        if form.is_valid() :
            category_name = form.cleaned_data['name']
            form.save()
            messages.success(request, f'{category_name} Category updated successfully')
            return redirect('category-management')
    else :
        form =   CategoryForm(instance=category)
        
    return render(request, 'admin_dash/edit_category.html',{'form':form,'category': category})



@login_required(login_url='admin-login')
def category_delete(request, category_id) :
    category = get_object_or_404(Category, id=category_id)
    category.is_available = not category.is_available
    category.save()
    if category.is_available :
        messages.info(request, f'{category.name} Category is unblocked')
        return redirect('category-management')
    else :
        messages.success(request, f'{category.name} Category is blocked')
        return redirect('category-management')
    



# --------------- Brand Management ---------------

@login_required(login_url='admin-login')
def brand_management(request) :
    query = request.GET.get('query')
    if query:
        all_brands = Brand.objects.filter(name__icontains=query).order_by('-id')
    else:
        all_brands = Brand.objects.all().order_by('-id')
    
    paginate_query = paginate_queryset(all_brands, request, 8)
    context = {
        'all_brands':paginate_query,
        'query':query
    }
    return render(request, 'admin_dash/brand_management.html',context)


@login_required(login_url='admin-login')
def add_brand(request) :
    if request.method == 'POST' :
        form = BrandForm(request.POST)
        if form.is_valid():
            form.save()
            brand_name = form.cleaned_data['name']
            messages.success(request, f'{brand_name} new brand succcessfully added')
            return redirect('brand-management')
    else:
        form = BrandForm()

    return render(request, 'admin_dash/add_brand.html', {'form':form})



@login_required(login_url='admin-login')
def update_brand(request, brand_id) :
    brand = get_object_or_404(Brand, id=brand_id)

    if request.method == 'POST' :
        form = BrandForm(request.POST,instance=brand)
        if form.is_valid():
            form.save()
            brand_name = form.cleaned_data['name']
            messages.success(request, f'{brand_name} is updated successfully.')
            return redirect('brand-management')
    else:
        form = BrandForm(instance=brand)

    return render(request, 'admin_dash/edit_brand.html', {'form':form, 'brand':brand})



@login_required(login_url='admin-login')
def delete_brand(request,brand_id):
    brand = get_object_or_404(Brand, id=brand_id)
    brand.is_available = not brand.is_available
    brand.save()
    if brand.is_available :
        messages.success(request, f"{brand.name} brand is available")
        return redirect('brand-management')
    else :
        messages.warning(request, f"{brand.name} Barnd is blocked ")
        return redirect('brand-management')
    


# --------------- Product Management ---------------

@login_required(login_url='admin-login')
def product_management(request) :
    query = request.GET.get('query')
    if query:
        all_products = Product.objects.filter(name__icontains=query).order_by('-id')
    else:
        all_products = Product.objects.all().order_by('-id')

    paginate_query = paginate_queryset(all_products, request, 10)
    context = { 
        'all_products': paginate_query,
        'query':query
        }
    return render(request, 'admin_dash/product_management.html',context)


@login_required(login_url='admin-login')
def add_product(request):
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)  
        if form.is_valid():
            product_name = form.cleaned_data['name']
            form.save()
            messages.success(request, f"{product_name} New product added successfully.")
            return redirect('product-management')
    else:
        form = ProductForm()  

    return render(request, 'admin_dash/add_product.html', {'form': form}) 


@login_required(login_url='admin-login')
def update_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            product_name = form.cleaned_data['name']
            form.save()            
            messages.success(request, f'{product_name} product is updated successfully.')
            return redirect('product-management')
    else:
        form = ProductForm(instance=product)

    return render(request, 'admin_dash/edit_product.html', {'form': form, 'product': product})




@login_required(login_url='admin-login')
def product_delete(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.is_available = not product.is_available  
    product.save()
    if product.is_available :
        messages.success(request, f'{product.name} Product is available')
        return redirect('product-management')
    else :
        messages.warning(request, f'{product.name} product is blocked')
        return redirect('product-management')



@login_required(login_url='admin-login')
def publish_products(request, product_id):
    try:
        product = Product.objects.get(id=product_id)
    except Product.DoesNotExist:
        messages.warning(request, 'product is not found')
        return redirect('product-management')
    
    if product.status == 'published':
        messages.warning(request, f'{product.name} is already published.')
        return redirect('product-management')
    
    if not Variants.objects.filter(product=product).exists():
        messages.warning(request, 'Please add product variant before publishing.')
        return redirect('product-management')
        
    if not Images.objects.filter(product=product).exists():
        messages.warning(request, 'Please add product photos before publishing.')
        return redirect('product-management')
    
    product.status = 'published'
    product.save()
    
    messages.success(request, f'{product.name} has been successfully published.')
    return redirect('product-management')
    


#  ---------------- Product variants ------------------

@login_required(login_url='admin-login')
def show_variants(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    image = Images.objects.filter(product=product)
    variants = Variants.objects.filter(product=product)

    context = {
        'product':product,
        'image':image,
        'variants':variants
    }
    return render(request, 'admin_dash/variants_product.html', context)


# ----------- Upload product image with fixed size -----
@login_required(login_url='admin-login')
def add_image_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)

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
            image.save()

            messages.success(request, 'Product Image added successfully')
            return redirect('show-variants', product_id=product_id)

    else:
        form = ImageForm()

    return render(request, 'admin_dash/add_image_product.html', {'form': form, 'product': product})


@login_required(login_url='admin-login')
def delete_product_image(request,img_id, product_id) :
    image = get_object_or_404(Images, id=img_id, product=product_id)
    image.delete()
    messages.success(request, 'Product Image Removed')
    return redirect('show-variants', product_id=product_id)


#-----------Add product size variants ----------

@login_required(login_url='admin-login')
def add_size_and_quantity(request, product_id) :
    product = get_object_or_404(Product, id=product_id)

    if request.method == 'POST' :
        form = ProductSizeVariantsForm(request.POST,  initial={'product': product})
        if form.is_valid():
            variant = form.save(commit=False)
            variant.product = product
            variant.save()
            messages.success(request, 'New size and quantity is updated')
            return redirect('show-variants',product_id=product_id)
    else:
        form = ProductSizeVariantsForm()
    return render(request, 'admin_dash/add_size_quantity.html', {'form':form})


@login_required(login_url='admin-login')
def update_size_of_quantity(request, variant_id):
    variant = get_object_or_404(Variants, id=variant_id)
    if request.method == 'POST':
        form = ProductSizeVariantsForm(request.POST, instance=variant, initial={'product': variant.product})
        if form.is_valid():
            form.save()
            messages.success(request, f'{variant.product.name} product size variant updated successfully')
            return redirect('show-variants',product_id=variant.product.id)
        
    else:
        form = ProductSizeVariantsForm(instance=variant, initial={'product': variant.product})
    return render(request, 'admin_dash/edit_size_quantity.html', {'form':form, 'variant':variant})



@login_required(login_url='admin-login')
def block_product_size(request, variant_id, product_id) :
    variant = get_object_or_404(Variants, id=variant_id, product=product_id)
    if variant.is_available == True:
        variant.is_available = False
        variant.save()
        messages.success(request, f'product size {variant.size } is blocked.')
        product_id = variant.product.id
        return redirect(reverse('show-variants', args=[product_id]))
    else:
        variant.is_available = True
        variant.save()
        messages.success(request, f'product size {variant.size } is unblocked.')
        product_id = variant.product.id
        return redirect(reverse('show-variants', args=[product_id]))


    
# ------------------ Orders Management ----------------

@login_required(login_url='admin-login')
def all_orders(request) :
    query = request.GET.get('query','').strip()
    print('query', query)
    if query:
        all_orders = Order.objects.filter(
            Q(tracking_no__icontains=query) | Q(fname__icontains=query) | Q(lname__icontains=query)    
        ).order_by('-created_at','-id')
    else:
        all_orders = Order.objects.order_by('-created_at','-id')

    paginate_query = paginate_queryset(all_orders, request, 10)
    orders_with_return = set(OrderItem.objects.filter(status='Return Requested').values_list('order_id', flat=True))
    context = {
        'all_orders': paginate_query,
        'orders_with_return': orders_with_return,
        }
    return render(request, 'admin_dash/all_orders.html',context)



@login_required(login_url='admin-login')
def view_all_order_items(request):
    time_range = request.GET.get('time_range', '')
    status = request.GET.get('status', '')
  
    if status:
        all_orders, total_amount_or_error = get_filtered_orders(time_range=time_range, status=status)
    else:
        all_orders, total_amount_or_error = get_filtered_orders(time_range=time_range)

    paginate_query = paginate_queryset(all_orders, request, 10)
    context = {
        'all_order_items':paginate_query,
        'status_choices': OrderItem.STATUS_CHOICES,
        'selected_time_range': time_range,
        'selected_status': status
    }
    return render(request, 'admin_dash/view_all_order_items.html', context )



@login_required(login_url='admin-login')
def view_single_order(request,ord_id):
    order = Order.objects.filter(id=ord_id).first()
    orderitems = OrderItem.objects.filter(order=order).order_by('-id')
     
    items_with_forward_statuses = []
    for item in orderitems:
        if item.status in STATUS_FLOW:
            current_index = STATUS_FLOW.index(item.status)
            forward_statuses = STATUS_FLOW[current_index+1:]
        else:
            forward_statuses = []  
        items_with_forward_statuses.append({
            'item': item,
            'forward_statuses': forward_statuses
        })

    cancellable_statuses = ['Pending', 'Confirmed', 'Out for Shipping', 'Shipped', 'Out for Delivery']
    cancellable_items = orderitems.filter(status__in=cancellable_statuses)
    can_cancel_all = cancellable_items.exists()

    context={
        'order':order,
        'orderitems':orderitems,
        'orderitems_with_statuses': items_with_forward_statuses,
        'can_cancel_all':can_cancel_all,
    }
    return render(request, 'admin_dash/view_single_order.html',context)



#------------- Update order item status -------------

@login_required(login_url='admin-login')
def update_single_order_status(request, ord_id):
    if request.method == 'POST':
        item_id = request.POST.get('item_id').strip()
        new_status = request.POST.get('status').strip()
        
        if not item_id or not new_status:
            messages.warning(request, "Item ID and status are required.")
            return redirect('view-single-order', ord_id=ord_id)
        
        if new_status not in STATUS_FLOW:
            messages.warning(request, "Invalid status selected. You can only update to a forward status.")
            return redirect('view-single-order', ord_id=ord_id)
        
        
        try:
            order = Order.objects.get(id=ord_id)
        except Order.DoesNotExist:
            messages.warning(request, "Something wrong. Order does not exist.")
            return redirect('view-single-order', ord_id=ord_id)
        
        try:
            order_item = OrderItem.objects.get(order=order, id=item_id)
        except OrderItem.DoesNotExist:
            messages.warning(request, "Order item not found.")
            return redirect('view-single-order', ord_id=ord_id)
        
        # prevent status to previous status
        current_status_index = STATUS_FLOW.index(order_item.status) if order_item.status in STATUS_FLOW else -1 
        new_status_index = STATUS_FLOW.index(new_status) 

        if new_status_index <= current_status_index:
            messages.warning(request, f"You cannot move status backward from '{order_item.status}' to '{new_status}'.")
            return redirect('view-single-order', ord_id=ord_id)
        
        if new_status == "Delivered":
            order_item.return_valid_until = date.today() + timedelta(days=7)

        order_item.status = new_status
        order_item.save()
        messages.success(request, f"Order item status updated to '{new_status}'.")
        return redirect('view-single-order',ord_id=ord_id)
    
    messages.warning(request, "Invalid request method.")
    return redirect('view-single-order', ord_id=ord_id)



#------------ Manage return order -------------

@login_required(login_url='admin-login')
def manage_return_request(request, ord_id):
    if request.method == 'POST':
        action = request.POST.get('action', '').strip()
        item_id = request.POST.get('item_id', '').strip()

        if action not in ['accept_return', 'reject_return']:
            messages.warning(request, "Invalid action. Cannot perform this operation.")
            return redirect('view-single-order', ord_id=ord_id)
        if not item_id:
            messages.warning(request, 'Order item ID missing. Please try again.')
            return redirect('view-single-order', ord_id=ord_id)

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=ord_id)
                order_item = OrderItem.objects.select_for_update().get(order=order, id=item_id)

                if order_item.status != 'Return Requested':
                    messages.warning(request, 'Only delivered and return requested item can be managed for return.')
                    return redirect('view-single-order', ord_id=ord_id)

                if action == 'accept_return':
                    # Update variant stock
                    variant = Variants.objects.select_for_update().filter(product=order_item.product,size=order_item.size).first()
                    if variant:
                        variant.quantity += order_item.quantity
                        variant.save()

                    # Refund to wallet
                    user_wallet, created = Wallet.objects.get_or_create(user=order.user)
                    
                    refund_amount = 0
                    if order.payment_mode in ['paid by razorpay', 'paid by wallet']:
                        total_price = Decimal(order_item.price * order_item.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        user_wallet.wallet += total_price
                        refund_amount = total_price
                        user_wallet.save()
                    
                        # Create payment history for tracking transaction
                        create_payment(
                            user=order.user,
                            order=order,
                            transaction_type='Refund',
                            amount=refund_amount,
                            payment_mode=order.payment_mode,
                            description= f"Return accepted for '{order_item.product.name}' (Qty: {order_item.quantity}) from Order {order.tracking_no}"
                        )
                        
                    # Update order item status
                    order_item.status = 'Returned'
                    order_item.save()

                    messages.success(request, f'{order_item.product.name} return request accepted.')
                    return redirect('view-single-order', ord_id=ord_id)

                else:  # reject_return
                    order_item.status = 'Return Rejected'
                    order_item.save()
                    messages.warning(request, f'{order_item.product.name} return request rejected.')
                    return redirect('view-single-order', ord_id=ord_id)

        except Order.DoesNotExist:
            messages.warning(request, "Order not found.")
        except OrderItem.DoesNotExist:
            messages.warning(request, "Order item not found.")
        except Exception as e:
            print(f"Error during return request handling: {e}")
            messages.warning(request, "Something went wrong while processing the return request.")

        return redirect('view-single-order', ord_id=ord_id)

    messages.warning(request, "Invalid request method.")
    return redirect('view-single-order', ord_id=ord_id)
        


# ----------------- Cancel single order item ------------------

@login_required(login_url='admin-login')
def cancel_single_order_by_admin(request, ord_id):
    if request.method == 'POST':
        cancel_reason = request.POST.get('cancel_reason','').strip()
        item_id = request.POST.get('item_id').strip()

        if not cancel_reason:
            messages.warning(request, "Cancel reason is required.")
            return redirect('view-single-order', ord_id=ord_id)
        if len(cancel_reason) < 10:
            messages.warning(request, "Cancel reason must be at least 10 characters. Please enter valid reason.")
            return redirect('view-single-order', ord_id=ord_id)
        if cancel_reason.isdigit() or re.fullmatch(r'[^\w\s]+', cancel_reason):
            messages.warning(request, "Cancel reason must contain valid text, not just digits or special characters.")
            return redirect('view-single-order', ord_id=ord_id)
        if not item_id:
            messages.warning(request, "Something went wrong with the order. Please try again later.")
            return redirect('view-single-order', ord_id=ord_id)

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=ord_id)
                order_item = OrderItem.objects.select_for_update().get(order=order, id=item_id)

                if order_item.status == 'Cancelled':
                    messages.warning(request, f'{order_item.product.name} is already cancelled.')
                    return redirect('view-single-order', ord_id=ord_id)

                # Update stock
                variant = Variants.objects.select_for_update().filter(product=order_item.product, size=order_item.size).first()
                if variant:
                    variant.quantity += order_item.quantity
                    variant.save()

                # Refund if needed
                user_wallet, created = Wallet.objects.get_or_create(user=order.user)
                # if user_wallet.wallet is None:
                #     user_wallet.wallet = 0
                refund_amount = 0
                if order.payment_mode in ['paid by razorpay', 'paid by wallet']:
                    total_price = Decimal(order_item.price * order_item.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    user_wallet.wallet += total_price
                    refund_amount = total_price
                    user_wallet.save()
                
                    # Create payment history for tracking transaction
                    create_payment(
                        user=order.user,
                        order=order,
                        transaction_type='Refund',
                        amount=refund_amount,
                        payment_mode=order.payment_mode,
                        description=f"Refund for cancellation of '{order_item.product.name}' (Qty: {order_item.quantity}) from Order {order.tracking_no}."
                    )

                # Update order item
                order_item.status = 'Cancelled'
                order_item.cancel_reason = cancel_reason
                order_item.cancelled_by = 'admin'
                order_item.save()
                
                messages.success(request, f'{order_item.product.name} has been cancelled successfully.')
                return redirect('view-single-order', ord_id=ord_id)

        except Order.DoesNotExist:
            messages.warning(request, "Order not found.")
        except OrderItem.DoesNotExist:
            messages.warning(request, "Order item not found.")
        except Exception as e:
            print(f" Error during single item cancellation: {e}")
            messages.error(request, "Something went wrong while cancelling the order item. Please try again.")
        
        return redirect('view-single-order', ord_id=ord_id)

    messages.warning(request, "Invalid request method.")
    return redirect('view-single-order', ord_id=ord_id)



#-----------------------  Cancel all order ------------------

@login_required(login_url='admin-login')
def cancel_all_order_by_admin(request, ord_id):
    if request.method == 'POST':
        cancel_reason = request.POST.get('cancel_reason', '').strip()

        if not cancel_reason:
            messages.warning(request, "Cancel reason is required.")
            return redirect('view-single-order', ord_id=ord_id)
        if len(cancel_reason) < 10:
            messages.warning(request, "Cancel reason must be at least 10 characters. Please enter valid reason.")
            return redirect('view-single-order', ord_id=ord_id)
        if cancel_reason.isdigit() or re.fullmatch(r'[^\w\s]+', cancel_reason):
            messages.warning(request, "Cancel reason must contain valid text, not just digits or special characters.")
            return redirect('view-single-order', ord_id=ord_id)

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(id=ord_id)

                user_wallet, created = Wallet.objects.get_or_create(user=order.user)
                # if user_wallet is None:
                #     raise Exception("User wallet is invalid.")

                cancellable_statuses = ['Pending', 'Confirmed', 'Out for Shipping', 'Shipped', 'Out for Delivery']
                order_items = OrderItem.objects.select_for_update().filter(order=order)
                cancellable_items = order_items.filter(status__in=cancellable_statuses)

                if not cancellable_items.exists():
                    raise Exception("No items in this order are eligible for cancellation.")

                # Update Variant stock
                for item in cancellable_items:
                    product = item.product
                    size = item.size
                    variant = Variants.objects.select_for_update().filter(product=product, size=size).first()
                    if variant:
                        variant.quantity += item.quantity
                        variant.save()

                # Refund if payment was online
                if order.payment_mode in ['paid by razorpay', 'paid by wallet']:
                    # if user_wallet.wallet is None:
                    #     user_wallet.wallet = 0
                    
                    total_refund = 0
                    for item in cancellable_items:
                        total_price_for_item = Decimal(item.price * item.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        user_wallet.wallet += total_price_for_item
                        total_refund += total_price_for_item
                    user_wallet.save()

                    # Create payment history for tracking transaction 
                    create_payment(
                        user=order.user,
                        order=order,
                        transaction_type='Refund',
                        amount=total_refund,
                        payment_mode=order.payment_mode,
                        description=f'Refund for cancelled items in Order {order.tracking_no}'
                    )

                # Update status & cancel reason
                for item in cancellable_items:
                    item.status = 'Cancelled'
                    item.cancel_reason = cancel_reason
                    item.cancelled_by = 'admin'
                    item.save()
                
                messages.success(request, f'This {order.tracking_no} all order is cancelled')
                return redirect('view-single-order', ord_id=ord_id)

        except Order.DoesNotExist:
            messages.warning(request, "Something wrong. Order does not exist")
            return redirect('view-single-order', ord_id=ord_id)
        except Exception as e:
            print("Error during cancellation:", str(e))
            messages.error(request, f"Failed to cancel order. Please try again later")
            return redirect('view-single-order', ord_id=ord_id)

    messages.warning(request, "Invalid request method.")
    return redirect('view-single-order', ord_id=ord_id)



# -------------------- Coupon Management ----------------

@login_required(login_url='admin-login')
def view_coupons(request) :
    query = request.GET.get('query', '').strip()
    if query:
        all_coupons = Coupon.objects.filter(coupon_code__icontains=query).order_by('-id')
    else:
        all_coupons = Coupon.objects.all().order_by('-id')
    paginate_query = paginate_queryset(all_coupons, request, 8)

    return render(request, 'admin_dash/coupon_management.html', {'all_coupons':paginate_query})


@login_required(login_url='admin-login')
def add_coupon(request) :
    if request.method=='POST' :
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon_code = form.cleaned_data['coupon_code']
            form.save()
            messages.success(request, f'{coupon_code} new coupon is created successfully.')
            return redirect('view-coupons')
    else:
        form = CouponForm()
    return render(request, 'admin_dash/add_coupon.html', {'form':form})


@login_required(login_url='admin-login')
def delete_coupon(request,c_id) :
    coupon = Coupon.objects.get(id=c_id) 
    if coupon.is_active==True :
        coupon.is_active=False
        coupon.save()
        messages.warning(request, 'Coupon is blocked')
        return redirect('view-coupons')
    else :
        coupon.is_active=True
        coupon.save()
        messages.success(request, 'Coupon is Unblocked')
        return redirect('view-coupons') 
    
    
# ------------------- Offer Management ------------------
@login_required(login_url='admin-login')
def view_offers(request) :
    query = request.GET.get('query', '').strip()
    if query:
        all_offers = Offer.objects.filter(title__icontains=query).order_by('-start_date', '-id')
    else:
        all_offers = Offer.objects.all().order_by('-start_date', '-id')
    paginate_query = paginate_queryset(all_offers, request, 8)
    return render(request, 'admin_dash/offer_management.html',{'all_offers':paginate_query, 'query':query})


@login_required(login_url='admin-login')
def add_offer(request):
    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            offer_title = form.cleaned_data['title']
            form.save()
            messages.success(request, f"{offer_title} new offer added successfully.")
            return redirect('view-offers')
    else:
        form = OfferForm()

    return render(request, 'admin_dash/add_offer.html', {'form': form})


@login_required(login_url='admin-login')
def delete_offer(request, off_id):
    offer = get_object_or_404(Offer, id=off_id)
    offer.is_block = not offer.is_block
    offer.save()

    if offer.is_block:
        messages.success(request, f"{offer.title} Offer is Blocked")
        return redirect('view-offers')  
    else:
        messages.success(request, f"{offer.title} Offer is Unblocked")
        return redirect('view-offers')  
    


# --------------- Category offer ( apply offer for category )----------------

@login_required(login_url='admin-login')
def view_category_offers(request) :
    query = request.GET.get('query', '').strip()
    if query:
        categories = Category.objects.filter(name__icontains=query, is_available=True).order_by('-id')
    else:
        categories = Category.objects.filter(is_available=True).order_by('-id')
    
    paginate_query = paginate_queryset(categories, request, 8)
    return render(request, 'admin_dash/category_offers.html',{'categories':paginate_query, 'query':query})



@login_required(login_url='admin-login')
def update_category_offer(request,c_id) :
    category = get_object_or_404(Category, id=c_id)
    if request.method == 'POST' :
        form = CategoryOfferForm(request.POST,instance=category)
        if form.is_valid() :
            form.save()
            
            products_in_category = Product.objects.filter(categories=category, is_available=True)
            for product in products_in_category :
                product.offer = category.offer
                product.save()
            messages.success(request, 'Offer applied for category')
            return redirect('view-category-offers')
    else :
        form = CategoryOfferForm(instance=category)

    return render(request, 'admin_dash/apply_offer_for_category.html', {'form':form,'category':category}) 


@login_required(login_url='admin-login')
def remove_category_offer(request,c_id) :
    category = get_object_or_404(Category,id=c_id)
    category.offer = None
    category.save()
    products_with_offer = Product.objects.filter(categories=category)
    for product in products_with_offer :
        product.offer = None
        product.save()
    messages.success(request, 'Category offer removed !')
    return redirect('view-category-offers')
   


# ---------------- Product Offer (apply offer for product ) ------------------

@login_required(login_url='admin-login')
def veiw_product_offers(request) :
    query = request.GET.get('query', '').strip()
    if query:
        products = Product.objects.filter(name__icontains=query, is_available=True).order_by('-id')
    else:
        products = Product.objects.filter(is_available=True).order_by('-id')
    paginate_query = paginate_queryset(products, request, 8)
    return render(request, 'admin_dash/product_offers.html',{'products':paginate_query, 'query':query})



@login_required(login_url='admin-login')
def update_product_offer(request,p_id) :
    product = get_object_or_404(Product,id=p_id) 
    if request.method == 'POST' :
        form = ProductOfferForm(request.POST,instance=product)
        if form.is_valid() :
            form.save()
            messages.success(request, 'Offer applied for Product')
            return redirect('view-product-offers')
    else :
        form = ProductOfferForm(instance=product)
    return render(request, 'admin_dash/apply_offer_for_product.html', {'form':form,'product':product})


@login_required(login_url='admin-login')
def remove_product_offer(request,p_id) :
    product = get_object_or_404(Product,id=p_id)
    product.offer = None
    product.save()
    messages.success(request, 'Product offer removed !')
    return redirect('view-product-offers')



# --------------- Banner Management ----------------

@login_required(login_url='admin-login')
def banner_management(request):
    all_banner = Banner.objects.exclude(banner__isnull=True)
    context = {
        'all_banner': all_banner,
    }
    return render(request, 'admin_dash/banner_management.html', context)


@login_required(login_url='admin-login')
def add_banner_image(request) :
    if request.method == 'POST' :
        form = BannerForm(request.POST, request.FILES)
        if form.is_valid() :  
            form.save()
            messages.success(request, "Banner successfully Added")
            return redirect('banner-management')
    else :
        form = BannerForm()  
    return render(request, 'admin_dash/add_banner.html',{'form':form})


@login_required(login_url='admin-login')
def delete_banner(request,b_id) :
    banner = get_object_or_404(Banner, id=b_id)
    if banner.is_available == True :
        banner.is_available = False
        banner.save()
        messages.success(request, 'Banner blocked !')
        return redirect('banner-management')
    else :
        banner.is_available = True
        banner.save()
        messages.success(request, 'Banner Unblocked ')
        return redirect('banner-management')



#-------------------- Dash board data ----------------------

@login_required(login_url='admin-login')
def dash_board(request) :
    total_products   = Product.objects.filter(is_available=True).count()
    total_revenue = OrderItem.objects.filter(status='Delivered').aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0

    today = timezone.now()
    start_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    monthly_revenue = OrderItem.objects.filter(status='Delivered', created_at__gte=start_of_month).aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0
   
    total_customers  = User.objects.filter(is_active=True,is_superuser=False).count()

    total_orders = (
        OrderItem.objects.aggregate(count=Count('id'))
    )['count'] or 0

    cod_count = Order.objects.filter(payment_mode='COD').count()
    razorpay_count = Order.objects.filter(payment_mode='paid by razorpay').count()
    wallet_count = Order.objects.filter(payment_mode='paid by wallet').count()
    
    context = {
        'total_products'  :total_products,
        'total_customers' :total_customers,
        'total_revenue'   : total_revenue,
        'monthly_revenue' : monthly_revenue,
        'total_orders'    : total_orders,
        'cod_count'       : cod_count,
        'razorpay_count'  : razorpay_count,
        'wallet_count'    : wallet_count,
    }
    return render(request, 'admin_dash/admin_dash.html',context)



def get_sales_data(request, period):
    if period == 'week':
        start_date = timezone.now().date() - timezone.timedelta(days=6)
        order_items = OrderItem.objects.filter(created_at__gte=start_date, status='Delivered')
        data = (
            order_items.annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(total=Sum(F('quantity') * F('price')))
            .order_by('day')
        )
        labels = [item['day'].strftime('%A') for item in data]
    elif period == 'month':
        start_date = timezone.now().date() - timezone.timedelta(days=30)
        order_items = OrderItem.objects.filter(created_at__gte=start_date, status='Delivered')
        data = (
            order_items.annotate(day=TruncDay('created_at'))
            .values('day')
            .annotate(total=Sum(F('quantity') * F('price')))
            .order_by('day')
        )
        labels = [item['day'].strftime('%Y-%m-%d') for item in data]
    elif period == 'year':
        start_date = timezone.now().date() - timezone.timedelta(days=365)
        order_items = OrderItem.objects.filter(created_at__gte=start_date, status='Delivered')
        data = (
            order_items.annotate(month=TruncMonth('created_at'))
            .values('month')
            .annotate(total=Sum(F('quantity') * F('price')))
            .order_by('month')
        )
        labels = [f"{item['month'].strftime('%B')}" for item in data]
    else:
        return JsonResponse({'error': 'Invalid period'})

    sales_data = [item['total'] for item in data]
    return JsonResponse({'labels': labels, 'data': sales_data})




@login_required(login_url='admin-login')
def view_sales_reports(request) :
   
    orders, total_amount_or_error = get_filtered_orders(
        time_range=request.GET.get('time_range'),
        start_date_input=request.GET.get('start_date'),
        end_date_input=request.GET.get('end_date'),
        status='Delivered'
    )

    if orders is None:
        messages.warning(request, total_amount_or_error)
        return redirect('view-sales-reports')
    
    paginate_data = paginate_queryset(orders, request, 10)
    
    context = {
        'orders': paginate_data,
        'selected_time_range': request.GET.get('time_range', 'all'),
        'total_amount':total_amount_or_error
    }

    return render(request, 'admin_dash/view_sales_reports.html', context)




# ------------- Generate sales report (PDF) -------------

@login_required(login_url='admin_log_in')
def download_pdf(request):
    time_range = request.GET.get('time_range')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    orders, total_amount_or_error = get_filtered_orders(
        time_range=time_range,
        start_date_input=start_date,
        end_date_input=end_date,
        status='Delivered'
    )

    if orders is None:
        return HttpResponse(total_amount_or_error, status=400)
    
    period = get_period_label(time_range)

    context = {
        'orders': orders,
        'total_sale_amount': total_amount_or_error,
        'time_range': period,
        'start_date': start_date,
        'end_date': end_date,
    }

    pdf = render_to_pdf('pdfs/salesreport.html', context)

    if pdf:
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = 'filename="sales_report.pdf"'
        return response

    return HttpResponse("Error generating PDF", status=500)