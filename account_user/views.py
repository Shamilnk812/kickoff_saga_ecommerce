import random
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from django.shortcuts import get_object_or_404, render,redirect
from cart.models import Order,OrderItem,Coupon
from admin_dash.models import Variants
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from .validators import *
from .helpers import render_to_pdf
from .forms import *
from .models import *
from django.contrib import messages
from django.core.exceptions import ValidationError
import re
from django.core.exceptions import ObjectDoesNotExist
from django.views.decorators.cache import never_cache
from django.db import transaction
from cart.utils import create_payment
from django.contrib.auth import logout
from decimal import Decimal, ROUND_HALF_UP

# ------------ View all orders (a specific user's order) -------------

@login_required(login_url='login')
def user_orders(request) :
    orders = Order.objects.filter(user=request.user).order_by('-id')
    context = {'orders':orders}
    return render(request, 'user_account/user_orders.html',context)



#---------------- View single order details --------------
@login_required(login_url='login')
def view_order(request,order_id) :
    order = Order.objects.filter(id=order_id, user=request.user).first()
    orderitems = OrderItem.objects.filter(order=order).order_by('id')
    cancellable_statuses = ['Pending', 'Confirmed', 'Out for Shipping', 'Shipped', 'Out for Delivery']
    cancellable_items = orderitems.filter(status__in=cancellable_statuses)
    can_cancel_all = cancellable_items.exists()

    context={
        'order':order,
        'orderitems':orderitems,
        'can_cancel_all': can_cancel_all,
    }
    return render(request,'user_account/view_single_order.html',context)



#--------------------- Cancel order ----------------------

@login_required(login_url='login')
def cancel_order(request, order_id):

    if request.method == 'POST':    
        cancel_reason = request.POST.get('cancel_reason', '').strip()

        if not cancel_reason:
            messages.error(request, "Cancel reason is required.")
            return redirect('order-detail', order_id=order_id)
        if len(cancel_reason) < 10:
            messages.error(request, "Cancel reason must be at least 10 characters.")
            return redirect('order-detail', order_id=order_id)
        if cancel_reason.isdigit() or re.fullmatch(r'[^\w\s]+', cancel_reason):
            messages.error(request, "Cancel reason must contain valid text.")
            return redirect('order-detail', order_id=order_id)

       
        try:
            with transaction.atomic():

                order = Order.objects.select_for_update().get(user=request.user, id=order_id)
                cancellable_statuses = ['Pending', 'Confirmed', 'Out for Shipping', 'Shipped', 'Out for Delivery']
                order_items = OrderItem.objects.filter(order=order)
                cancellable_items = order_items.filter(status__in=cancellable_statuses)

                if not cancellable_items.exists():
                    messages.error(request, "No items in this order are eligible for cancellation.")
                    return redirect('order-detail', order_id=order_id)

                user_wallet, created = Wallet.objects.get_or_create(user=request.user)

                # Product variants restoring
                for item in cancellable_items:
                    product = item.product
                    size = item.size
                    variant = Variants.objects.filter(product=product, size=size).first()
                    if variant:
                        variant.quantity += item.quantity
                        variant.save()

                # Update user wallet if that paid by razorypay or wallet
                if order.payment_mode == 'paid by razorpay' or order.payment_mode == 'paid by wallet':
                    total_refund = 0
                    for item in cancellable_items:
                        item_total_price = Decimal(item.price * item.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                        user_wallet.wallet += item_total_price
                        total_refund += item_total_price
                    user_wallet.save()

                    # Create payment for tracking payment history
                    create_payment(
                        user=request.user,
                        order=order,
                        transaction_type='Refund',
                        amount=total_refund,
                        payment_mode=order.payment_mode,
                        description=f'Refund for cancelled items in Order {order.tracking_no}'
                    )


                for item in cancellable_items:
                    item.status = 'Cancelled'
                    item.cancel_reason = cancel_reason
                    item.cancelled_by = 'user'
                    item.save()
                
        except Exception as e:
            messages.error(request, f"An error occurred while canceling the order")
            return redirect('order-detail', order_id=order_id)

        messages.success(request, 'Order canceled successfully.')
        return redirect('order-detail', order_id=order_id)
    


@login_required(login_url='login')
def cancel_single_item(request, order_id):
    if request.method == 'POST':
        cancel_reason = request.POST.get('cancel_reason', '').strip()
        item_id = request.POST.get('item_id')

        if not cancel_reason:
            messages.error(request, "Cancel reason is required.")
            return redirect('order-detail', order_id=order_id)
        if len(cancel_reason) < 10:
            messages.error(request, "Cancel reason must be at least 10 characters.")
            return redirect('order-detail', order_id=order_id)
        if cancel_reason.isdigit() or re.fullmatch(r'[^\w\s]+', cancel_reason):
            messages.error(request, "Cancel reason must contain valid text.")
            return redirect('order-detail', order_id=order_id)
        if not item_id:
            messages.error(request, "Something went wrong. Please try again later.")
            return redirect('order-detail', order_id=order_id)

        try:
            with transaction.atomic():
                order = Order.objects.select_for_update().get(user=request.user, id=order_id)
                order_item = OrderItem.objects.select_for_update().get(order=order, id=item_id)

                cancellable_statuses = ['Pending', 'Confirmed', 'Out for Shipping', 'Shipped', 'Out for Delivery']
                if order_item.status not in cancellable_statuses:
                    messages.error(request, "You cannot cancel this item at its current status.")
                    return redirect('order-detail', order_id=order_id)

                # Restore product variants 
                item_variants = Variants.objects.select_for_update().filter(
                    product=order_item.product, size=order_item.size
                ).first()
                if item_variants:
                    item_variants.quantity += order_item.quantity
                    item_variants.save()

                # Update user wallet if that paid by razorypay or wallet
                user_wallet, _ = Wallet.objects.get_or_create(user=request.user)
                refund_amount = 0
                if order.payment_mode in ['paid by razorpay', 'paid by wallet']:
                    # if user_wallet.wallet is None:
                    #     user_wallet.wallet = 0
                    refund_amount = Decimal(order_item.price * order_item.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    user_wallet.wallet += refund_amount
                    user_wallet.save()
                    
                    # Create transaction history
                    create_payment(
                        user=request.user,
                        order=order,
                        transaction_type='Refund',
                        amount=refund_amount,
                        payment_mode=order.payment_mode,
                        description=f"Refund for cancellation of '{order_item.product.name}' (Qty: {order_item.quantity}) from Order {order.tracking_no}."
                    )

                # Update order item
                order_item.cancel_reason = cancel_reason
                order_item.status = 'Cancelled'
                order_item.cancelled_by = 'user'
                order_item.save()

                messages.success(request, "Item cancelled successfully. Refund processed if applicable.")
                return redirect('order-detail', order_id=order_id)

        except Order.DoesNotExist:
            messages.error(request, "Order not found or doesn't belong to you.")
        except OrderItem.DoesNotExist:
            messages.error(request, "The item you are trying to cancel does not exist in your order.")
        except Exception as e:
            print('erorr', e)
            messages.error(request, "An unexpected lkjjklklk;lerror occurred during cancellation")

        return redirect('order-detail', order_id=order_id)
    

       


#--------------------- Return Order -------------------

@login_required(login_url='login')
def return_single_item(request, order_id):
    if request.method == 'POST':
        item_id = request.POST.get('item_id')
        return_reason = request.POST.get('return_reason').strip()
        
        if not return_reason:
            messages.error(request, "Return reason is required.")
            return redirect('order-detail', order_id=order_id)
        if len(return_reason) < 10:
            messages.error(request, "Return reason must be at least 10 characters. Please enter valid reason.")
            return redirect('order-detail', order_id=order_id)
        if return_reason.isdigit() or re.fullmatch(r'[^\w\s]+', return_reason):
            messages.error(request, "Return reason must contain valid text, not just digits or special characters.")
            return redirect('order-detail', order_id=order_id)
        if not item_id :
            messages.error(request, "somthing wrong with order. Please try again later")
            return redirect('order-detail', order_id=order_id)
        
        try:
            order = Order.objects.get(user=request.user,id=order_id)
        except Order.DoesNotExist:
            messages.error(request, "Order not found or does not belong to you.")
            return redirect('order-detail', order_id=order_id)
        
        try:
            order_item = OrderItem.objects.get(order=order,id=item_id)
        except OrderItem.DoesNotExist:
            messages.error(request, "The item you are trying to cancel does not exist in your order.")
            return redirect('order-detail', order_id=order_id)
        
        if order_item.status == 'Delivered':
            order_item.status = 'Return Requested'
            order_item.return_reason = return_reason
            order_item.save()
            messages.success(request, "Return request submitted successfully.")
        else:
             messages.error(request, f"This item cannot be returned because it is currently marked as '{order_item.status}'.")
        
        return redirect('order-detail', order_id=order_id)

        

    
# --------------------- View user wallet and coupons -------------------

@login_required(login_url='login')
def user_wallet(request):
    coupons = Coupon.objects.filter(is_active=True) 
    try:
        wallet_instance = Wallet.objects.get(user=request.user)
    except ObjectDoesNotExist:
        wallet_instance = Wallet.objects.create(user=request.user)

    context = {'wallet': wallet_instance,'coupons':coupons}
    return render(request, 'user_account/wallet_show.html', context)
    


# ----------------- User addresss management --------------

@login_required(login_url='login')
def user_address(request) :
    new_address = Address.objects.filter(user=request.user).order_by('-id')
    context = {
        'new_address':new_address
    }
    return render(request, 'user_account/user_address.html',context)


@login_required(login_url='login')
def edit_address(request,ad_id) :
    address = Address.objects.get(id=ad_id)
    context ={
        'address':address
    }

    return render(request, 'user_account/edit_address.html',context)


@login_required(login_url='login')
def update_address(request,ad_id) :
    if request.method == 'POST' :
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        email = request.POST.get('email')
        city = request.POST.get('city')
        state = request.POST.get('state')
        country = request.POST.get('country')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        pincode = request.POST.get('pincode')

        if fname.strip()=='' or lname.strip()=='' or email.strip()=='' or phone.strip()=='' or address.strip()=='' or city.strip()=='' or state.strip()=='' or country.strip()=='' or pincode.strip()=='' :
            messages.error(request, "Fields cannot be empty!")
            return redirect('address-edit',ad_id=ad_id)
        
        if not all(map(is_alpha, [fname, lname, city, state, country])):
            messages.error(request, "Name, city, state, and country must contain only alphabets!")
            return redirect('address-edit', ad_id=ad_id)

        if not is_valid_phone(phone):
            messages.error(request, "Enter a valid 10-digit mobile number!")
            return redirect('address-edit', ad_id=ad_id)

        if not is_valid_pincode(pincode):
            messages.error(request, "Enter a valid 6-digit pincode!")
            return redirect('address-edit', ad_id=ad_id)

        new_address = Address.objects.get(id=ad_id)
        new_address.fname = fname
        new_address.lname = lname
        new_address.email = email
        new_address.city = city
        new_address.state = state
        new_address.country = country
        new_address.phone = phone
        new_address.address = address
        new_address.pincode = pincode
        new_address.save()
        messages.success(request, 'Your address has been updated successfully!')
        return redirect('addresses')
  
    return render(request, 'user_account/edit_address.html')



@login_required(login_url='login')
def delete_user_address(request, ad_id) :
    address = get_object_or_404(Address, id=ad_id) 
    address.delete()
    messages.success(request, "You address is deleted !")
    return redirect('addresses')
   

@login_required(login_url='login')
def account_details(request):
    if request.method == "POST":
        if 'update_info' in request.POST:  
            user_form = UserUpdateForm(request.POST, instance=request.user)
            password_form = ChangePasswordForm()
            if user_form.is_valid():
                user_form.save()
                messages.success(request, 'User info updated.')
                return redirect('account-details') 
          

        elif 'change_password' in request.POST:
            user_form = UserUpdateForm(instance=request.user)
            password_form = ChangePasswordForm(request.POST)
            if password_form.is_valid():
                user = request.user
                current_password = password_form.cleaned_data['current_password']
                new_password = password_form.cleaned_data['new_password']

                if user.check_password(current_password):
                    user.set_password(new_password)
                    user.save()
                    logout(request)
                    messages.success(request, 'Password updated successfully. Please log in again.')
                    return redirect(reverse('login'))
                else:
                    messages.error(request, 'Your current password is incorrect')
                    return redirect('account-details') 
                        
    else:
        user_form = UserUpdateForm(instance=request.user)
        password_form = ChangePasswordForm()

    return render(request, 'user_account/account_details.html', {
        'user_form': user_form,
        'password_form': password_form,
    })



#--------------- Transactoin History -------------
def Transaction_histroy(request):
    payment_history = PaymentHistory.objects.filter(user=request.user).order_by('-timestamp')
    return render(request, 'user_account/payment_history.html', {'payment_history':payment_history})



# ---------------- Download invoice -------------

def generate_invoice(request, order_id, order_item_id):
    # Get the order and order item
    order = get_object_or_404(Order, id=order_id)
    order_item = get_object_or_404(OrderItem, id=order_item_id, order=order)

    # Check if delivered
    if order_item.status != 'Delivered':
        messages.error(request, "Invoice can only be generated for delivered items.")
        return redirect('order-detail', order_id=order_id)
        
    invoice_number = str(random.randint(100000, 999999))
    context = {
        'order': order,
        'order_item': order_item,
        'invoice_number': invoice_number,
    }

    pdf = render_to_pdf('pdfs/invoice.html', context)
    if pdf:
        filename = f"invoice_{order.id}_{order_item.id}.pdf"
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{filename}"'
        return response
    messages.error(request, 'Failed to generate the invoice. Please try agin later')
    return redirect('order-detail', order_id=order_id)
