import re
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from admin_dash.models import Product,Variants
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *
from .utils import *
from django.db import transaction
from django.db.models import Sum
from account_user.models import Address,Wallet
from django.http import JsonResponse
import json
import random
from account_user.validators import *
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import never_cache



# ----------- Cart ------------
@login_required(login_url='log_in')
def view_cart(request):
    if request.user.is_authenticated:
        carts = Cart.objects.filter(user=request.user)
        total_cost = Cart.total_cost_for_user(request.user)

        applied_coupon_code = request.session.get('coupon_code')
        coupon = Coupon.objects.filter(coupon_code=applied_coupon_code, is_active=True).first()
        
        coupon_discount = 0
        applied_coupon = None 
        if coupon:
            if total_cost >= coupon.minimum_amount:
                coupon_discount = coupon.calculate_discount(total_cost)
                applied_coupon = applied_coupon_code
            else:
                request.session.pop('coupon_code', None)
                existing_coupon = UsedCoupon.objects.filter(user=request.user, used_coupon_code=applied_coupon_code)
                if existing_coupon:
                    existing_coupon.delete()
                messages.warning(request, 'Coupon removed: Cart total below minimum.')

        total_amount = total_cost - coupon_discount

        # apply and validate coupon 
        if request.method == 'POST':
            coupon_code = request.POST.get('coupon')
            coupon  = Coupon.objects.filter(coupon_code__icontains=coupon_code).first()
            

            if not coupon:
                messages.warning(request, 'Invalid coupon code.')
                return redirect('view_cart')

            if total_cost < coupon.minimum_amount:
                messages.warning(request, f'Cart must be above ₹{coupon.minimum_amount} to use this coupon.')
                return redirect('view_cart')
            
            if UsedCoupon.objects.filter(user=request.user, used_coupon_code=coupon_code).exists():
                messages.warning(request, 'You already used this coupon.')
                return redirect('view_cart')
            
            if not coupon.is_active:
                messages.warning(request, 'Coupon expired.')
                return redirect('view_cart')

            request.session['coupon_code'] = coupon_code
            UsedCoupon.objects.create(user=request.user, used_coupon_code=coupon_code)

            messages.success(request, "Coupon Applied")
            return redirect('view_cart')
        
      
        total_saved_amount = 0 
        for cart_item in carts:
            if cart_item.is_valid_cart_item and cart_item.product.offer and cart_item.product.offer.is_valid:
                total_saved_amount += cart_item.product.offer_save_amount() * cart_item.product_qty
        
        
        context = {
            'cart': carts,
            'total_amount': total_amount,
            'sub_total': total_cost,
            'total_saved_amount': total_saved_amount,
            'coupon_discount':coupon_discount,
            'applied_coupon':applied_coupon,
            'coupon_discount_percentage':coupon.discount_percentage if coupon else 0,
        }
        return render(request, 'cart/view_cart.html', context)

    else:
        return redirect('log_in')



@login_required(login_url='log_in')
def remove_coupon(request): 
    applied_coupon_code = request.session.get('coupon_code')
    
    if applied_coupon_code:
        request.session.pop('coupon_code', None)
        used_coupon = UsedCoupon.objects.filter(used_coupon_code=applied_coupon_code,user=request.user)
        used_coupon.delete()
        messages.success(request, 'Coupon Removed')
    else:
        messages.warning(request, 'No coupon applied')

    return redirect('view_cart')


#----------- Add to cart ----------
def add_to_cart(request):
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        if request.user.is_authenticated:
            data = json.loads(request.body)  
            product_qty = int(data['product_qty']) 
            product_id = data['pid']
            selected_size = data['size']
            product = Product.objects.get(id=product_id)

            try:
                variant = Variants.objects.get(product=product, size=selected_size)
                if variant.quantity >= product_qty:
                   
                    # Check if the product already exists in the user's cart
                    existing_cart = Cart.objects.filter(user=request.user, product=product, size=selected_size)
                    if existing_cart.exists():
                        return JsonResponse({'status': 'Product already in cart!'}, status=200)
                    else:
                        Cart.objects.create(user=request.user, product=product, product_qty=product_qty, size=selected_size)
                        return JsonResponse({'status': 'Product added to cart'}, status=200)
                else:
                    return JsonResponse({'status': 'Product stock not available'}, status=200)
            except Variants.DoesNotExist:
                return JsonResponse({'status': 'Selected size not available for this product'}, status=200)
            except Product.DoesNotExist:
                return JsonResponse({'status': 'Product not found'}, status=200)
        else:
            return JsonResponse({'status': 'Login to add to cart'}, status=200)
    else:
        return JsonResponse({'status': 'Invalid Access'}, status=200)
    


@login_required(login_url='log_in')
def remove_cart_item(request, cart_id):
    try:
        cart_item = get_object_or_404(Cart, id=cart_id)
        cart_item.delete()
        messages.success(request, 'Your cart item removed')
        return HttpResponseRedirect(reverse('view_cart'))
    except Cart.DoesNotExist:
        return HttpResponse("Cart item not found.", status=404)
    except Exception as e:
        return HttpResponse("An error occurred while removing the item.", status=500)
    


#------------- Update cart items ---------------
def update_cart(request):
    if request.method == 'POST':
        updated_items = 0

        for key, value in request.POST.items():
            if key.startswith('quantity_'):
                item_id = key.split('_')[1]
                new_quantity = int(value)

                try:
                    cart_item = Cart.objects.get(id=item_id)
                    # Check for size-based stock availability
                    product = cart_item.product
                    size = cart_item.size

                    try:
                        variant = Variants.objects.get(product=product, size=size)
                        if variant.quantity >= new_quantity:
                            
                            cart_item.product_qty = new_quantity
                            cart_item.save()
                            updated_items += 1
                        else:
                            messages.error(request, f'Only {variant.quantity} items available in size {size} for {product.name}.')
                    except Variants.DoesNotExist:
                        messages.error(request, f'Variant with size {size} for {product.name} not found.')

                except Cart.DoesNotExist:
                    messages.error(request, f'The item you are trying to update does not exist in your cart.')

        if updated_items > 0:
            messages.success(request, 'Your cart has been updated successfully.')

    return redirect('view_cart') 



#---------- Wishlist management ------------
def add_to_wishlist(request):
    if request.method == 'POST':
        if request.user.is_authenticated :
            product_id = request.POST.get('product_id')
            product = Product.objects.get(id=product_id)
            if Wishlist.objects.filter(product=product).exists() :
                return JsonResponse({'error': 'Product already in your wishlist'})
            else :
                Wishlist.objects.create(user=request.user,product=product)
            return JsonResponse({'message': 'Product added to wishlist successfully'})
        else :
            return JsonResponse({'error': 'Please login to add to wishlist'})

    else:
        return JsonResponse({'error': 'Invalid request method'})
    

def view_wishlist(request) :
    wishlist_items = Wishlist.objects.filter(user=request.user)
    wishlist_items = wishlist_items.annotate(total_quantity=Sum('product__variants__quantity'))
    return render(request, 'cart/wishlist.html',{'wishlist_items':wishlist_items})


def remove_wishlist_product(request,p_id) :
    product = get_object_or_404(Wishlist,product=p_id)
    product.delete()
    messages.success(request, 'Product removed from wishlist')
    return HttpResponseRedirect(reverse('view_wishlist'))

    
# ----------------- Checkout -----------------
@never_cache
@login_required(login_url='log_in')
def check_out(request):

    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        return redirect(reverse('home'))
    
    # Check if nay item is unavailable
    unavailable_items = [item for item in cart_items if not item.is_valid_cart_item]
    if unavailable_items:
        messages.error(request, "Some items in your cart are no longer available. Please remove them before proceeding to checkout.")
        return redirect(reverse('view_cart'))
    
    # Check if any item is out of stock
    out_of_stock_items = [item for item in cart_items if not item.is_in_stock]
    if out_of_stock_items:
        messages.error(request, "Some item in your cart are out of stock. Please update your cart before proceeding to checkout.")
        return redirect(reverse('view_cart'))  
    
    total_amount = sum(item.total_cost for item in cart_items)
    total_price = total_amount 
  
    # check if the coupon is exist and show the coupon and discount amount
    applied_coupon_code = request.session.get('coupon_code')
    coupon = Coupon.objects.filter(coupon_code=applied_coupon_code, is_active=True).first()
        
    coupon_discount = 0
    applied_coupon = None 
    if coupon:
        if total_price >= coupon.minimum_amount:
            coupon_discount = coupon.calculate_discount(total_price)
            applied_coupon = applied_coupon_code
            total_price = total_price - coupon_discount
 
    total_saved_amount = 0  

    for cart in cart_items:
        if cart.product.offer and cart.product.offer.is_valid:
            total_saved_amount += cart.product.offer_save_amount() * cart.product_qty
    
    # Add shipping  cost 
    shipping_cost = request.session.get('shipping_amount', 0)
    shipping_type = request.session.get('shipping_type')
    total_price = total_price + int(shipping_cost)


    # address = Address.objects.filter(user=request.user).last()
    addresses = Address.objects.filter(user=request.user)
    context = {
        'cart_items': cart_items,
        'total_price': max(total_price, 0), 
        'sub_total': total_amount,
        'addresses': addresses ,
        'total_saved_amount': total_saved_amount,
        'applied_coupon':applied_coupon,
        'coupon_discount':coupon_discount,
        'coupon_discount_percentage':coupon.discount_percentage if coupon else 0,
    }

    return render(request, 'cart/checkout.html', context)
    


# ----------- Check user wallet --------------
@login_required(login_url='log_in')
def check_wallet_balance(request):
    user_wallet = Wallet.objects.get(user=request.user)
    total_price = float(request.POST.get('total_price', 0))  

    if user_wallet.wallet >= total_price:
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})



# ---------------- Update shipping type ---------------
@csrf_exempt
def update_shipping(request):
    if request.method == "POST":
        print('heeeeeey bor ')
        try:
            data = json.loads(request.body)
            shipping_type = data.get("shipping_type")
            shipping_amount = data.get("shipping_amount")

            print('shippping type',shipping_type)
            print('shiping amount', shipping_amount)
            # Validate and convert amount
            try:
                shipping_amount = int(shipping_amount)
            except (TypeError, ValueError):
                shipping_amount = 0

            request.session['shipping_type'] = shipping_type
            request.session['shipping_amount'] = shipping_amount

            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "invalid request"}, status=405)
    



#------------------ Place order ------------------
@never_cache
@transaction.atomic
@login_required(login_url='log_in')
def place_order(request):
    if request.method == 'POST':

        user = request.user
        address = handle_address_submission(request)
        if not address:
            return redirect('checkout')
        
        cart_items = Cart.objects.select_related('product').filter(user=user)
        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('checkout')
        
        # Check if any items is unavailable 
        unavailable_items = [item for item in cart_items if not item.is_valid_cart_item]
        if unavailable_items:
            messages.error(request, "Your cart is contains unavailable items. Plese romove it")
            return redirect('checkout')
        

        # Checking the order items stock
        for item in cart_items:
            variant = Variants.objects.select_for_update().filter(product=item.product, size=item.size).first()
            if not variant or variant.quantity < item.product_qty:
                messages.error(request, f"Insufficient stock for {item.product.name} (Size: {item.size}).")
                return redirect('checkout')
        
        # Add shipping cost
        cart_original_total = sum(item.total_cost for item in cart_items)
        cart_total_price = cart_original_total
        shipping_type = request.session.get('shipping_type')
        shipping_cost = request.session.get('shipping_amount', 0)
        cart_total_price += int(shipping_cost)

        # Calculate total and apply coupon discount (if coupon exist)
        applied_coupon_code = request.session.get('coupon_code')
        coupon_discount, coupon_obj = apply_coupon(applied_coupon_code, cart_total_price)
        cart_total_price -= coupon_discount
        
        # Calculate the total saved amount (offer)
        total_offer_saved_amount = 0  
        for cart in cart_items:
            if cart.product.offer and cart.product.offer.is_valid:
                total_offer_saved_amount += cart.product.offer_save_amount() * cart.product_qty 

        # Check wallet balance 
        if request.POST.get('payment_mode') == 'paid by wallet':
            wallet = Wallet.objects.select_for_update().get(user=user)
            if wallet.wallet < cart_total_price:
                messages.error(request, "Insufficient wallet balance.")
                return redirect('checkout')
            wallet.wallet -= cart_total_price
            wallet.save()
        
        # Create order 
        order = create_order(user, address, cart_total_price, request.POST, coupon_discount, total_offer_saved_amount, shipping_type,shipping_cost)

        for item in cart_items:
            create_order_item(order, item, cart_original_total, coupon_discount)
        
        # Create payment for tracking payment history
        if request.POST.get('payment_mode') in ['paid by razorpay', 'paid by wallet']:
            create_payment(
                user=user,
                order=order,
                transaction_type='Debit',
                amount=cart_total_price,
                payment_mode=request.POST.get('payment_mode'),
                description=f'Order payment for order ID {order.tracking_no}'
            )
        
        # Clear the cart items and coupon (if exist)
        Cart.objects.filter(user=user).delete()
        request.session.pop('shipping_type',None)
        request.session.pop('shipping_amount', None)
        if coupon_obj:
            UsedCoupon.objects.filter(used_coupon_code=coupon_obj.coupon_code, user=user).delete()
        request.session.pop('coupon_code', None)
        return redirect('order_confirmation')
    

        # return render(request, 'cart/order_confirmation.html')



@login_required
def order_confirmation(request) :
    return render(request, 'cart/order_confirmation.html')