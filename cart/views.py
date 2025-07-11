import re
from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse
from admin_dash.models import Product,Variants
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import *
from .forms import *
from django.db.models import Sum
from account_user.models import Address,Wallet
from django.http import JsonResponse
import json
import random
from account_user.validators import *
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt



@login_required(login_url='log_in')
def view_cart(request):
    if request.user.is_authenticated:
        carts = Cart.objects.filter(user=request.user)
        total_cost_user_carts = Cart.total_cost_for_user(request.user)
        coupon_discount = 0

      
        if any(cart.coupon for cart in carts if cart.coupon):
            coupon_discount = carts.first().coupon.discound_amount if carts.first().coupon else 0

        total_amount = total_cost_user_carts - coupon_discount

        # apply and validate coupon 
        if request.method == 'POST':
            coupon_code = request.POST.get('coupon')
            coupon_obj  = Coupon.objects.filter(coupon_code__icontains=coupon_code)
           

            if not coupon_obj.exists():
                messages.warning(request, 'Invalid Coupon')
                return redirect('view_cart')
            
            if total_cost_user_carts < coupon_obj.first().minimum_amount:
                messages.warning(request, f'Amount should be greater than {coupon_obj.first().minimum_amount}')
                return redirect('view_cart')

            
            if UsedCoupon.objects.filter(used_coupon_code__icontains=coupon_code,user=request.user).exists() :
                messages.warning(request, 'This coupon alredy taken')
                return redirect('view_cart')
            else :
                UsedCoupon.objects.create(used_coupon_code=coupon_code,user=request.user)

            
            if coupon_obj.exists() and coupon_obj.first().is_expired:
                messages.warning(request, 'Coupon Expired!')
                return redirect('view_cart')
            
            if any(cart.coupon for cart in carts if cart.coupon):
                messages.warning(request, 'A coupon is already applied to your cart.')
                return redirect('view_cart')
            # Remove the existing coupon from all items in the cart
            for cart in carts:
                if cart.coupon:
                    total_amount += cart.coupon.discound_amount  # Add back coupon discount amount to total
                    cart.coupon = None
                    cart.save()

            # Apply the new coupon to all items in the cart
            for cart in carts:
                cart.coupon = coupon_obj.first()
                cart.save()

            messages.success(request, "Coupon Applied")
            return redirect('view_cart')
        
        # Check if the total amount is below the required minimum for any cart item with a coupon.
        # If so, remove the coupon from all cart items and restore the discount to the total amount.
        if any(cart.coupon and total_amount < cart.coupon.minimum_amount for cart in carts):
            for cart in carts:
                if cart.coupon:
                    total_amount += cart.coupon.discound_amount
                    cart.coupon = None
                    cart.save()
            messages.warning(request, 'Coupon removed as cart total fell below the minimum amount.')

        
        total_saved_amount = 0  # Initialize the total saved amount

        for cart_item in carts:
           
            if cart_item.product.offer and cart_item.product.offer.is_valid:
                total_saved_amount += cart_item.product.offer_save_amount() * cart_item.product_qty
        
        
        context = {
            'cart': carts,
            'total_amount': total_amount,
            'total_saved_amount': total_saved_amount
        }
        return render(request, 'cart/view_cart.html', context)

    else:
        return redirect('log_in')



@login_required(login_url='log_in')
def remove_coupon(request, cart_id):
    
    cart = get_object_or_404(Cart, id=cart_id, user=request.user)
    # Check if a coupon is applied before removing it
    if cart.coupon: 
        # Iterate through all carts associated with the user and remove the coupon
        user_carts = Cart.objects.filter(user=request.user)
        for user_cart in user_carts:
            if user_cart.coupon:
                user_cart.coupon = None
                user_cart.save()
        
        # Remove coupon from used coupon 
        used_coupon = UsedCoupon.objects.filter(used_coupon_code=cart.coupon.coupon_code,user=request.user)
        used_coupon.delete()
        messages.success(request, 'Coupon Removed from all carts')
    else:
        messages.warning(request, 'No coupon applied')

    return redirect('view_cart')


#----------------------- Add to cart -----------------
# @login_required(login_url='log_in')
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
    


#------------------ Remove form cart ----------------------
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
    


#-------------------- Update cart items ----------------------
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
                    messages.error(request, f'Cart item with ID {item_id} does not exist.')

        if updated_items > 0:
            messages.success(request, 'Your cart has been updated successfully.')

    return redirect('view_cart') 



#----------------------- Wishlist management ----------------


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

    
# ------------------------ Checkout -----------------
def check_out(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        return redirect(reverse('home'))
    
    # Check if any item is out of stock
    out_of_stock_items = [item for item in cart_items if not item.is_in_stock]
    if out_of_stock_items:
        messages.error(request, "Some item in your cart are out of stock. Please update your cart before proceeding to checkout.")
        return redirect(reverse('view_cart'))  
    
    total_price = sum(item.total_cost for item in cart_items)


    coupon_exists = any(item.coupon for item in cart_items if item.coupon)

    if coupon_exists:
        for item in cart_items:
            if item.coupon:
                total_price -= item.coupon.discound_amount
                break
    total_saved_amount = 0  # Initialize the total saved amount

    for cart in cart_items:
        if cart.product.offer and cart.product.offer.is_valid:
            total_saved_amount += cart.product.offer_save_amount() * cart.product_qty  

    address = Address.objects.filter(user=request.user).last()
    context = {
        'cart_items': cart_items,
        'total_price': max(total_price, 0), 
        'address': address,
        'total_saved_amount': total_saved_amount
    }

    return render(request, 'cart/checkout.html', context)


@login_required(login_url='log_in')
def razorpaycheck(request):
    cart = Cart.objects.filter(user=request.user)
    total_price = 0
    for item in cart:
        total_price += item.product.price * item.product_qty

    return JsonResponse({
        'total_price': total_price
    })


# ------------- Check user wallet ----------------

@login_required(login_url='log_in')
def check_wallet_balance(request):
    user_wallet = Wallet.objects.get(user=request.user)
    total_price = float(request.POST.get('total_price', 0))  

    if user_wallet.wallet >= total_price:
        return JsonResponse({'success': True})
    else:
        return JsonResponse({'success': False})
    

#------------------ Place order ---------------
@login_required(login_url='log_in')
def place_order(request):
    if request.method == 'POST':
        address_id = request.POST.get('address_id')  

        if address_id:
            selected_address = Address.objects.get(id=address_id)
            print(selected_address)
        else:
            user=request.user
            fname=request.POST.get('fname')
            lname=request.POST.get('lname')
            email=request.POST.get('email')
            phone=request.POST.get('phone')
            address=request.POST.get('address')
            city=request.POST.get('city')
            state=request.POST.get('state')
            country=request.POST.get('country')
            pincode=request.POST.get('pincode')
           
            if fname.strip()=='' or lname.strip()=='' or email.strip()=='' or phone.strip()=='' or address.strip()=='' or city.strip()=='' or state.strip()=='' or country.strip()=='' or pincode.strip()=='' :
                messages.error(request, "Plaese add a valid address, complete all required fields ")
                return redirect('checkout')
            
            if not all(map(is_alpha, [fname, lname, city, state, country])):
                messages.error(request, "Name, city, state, and country must contain only alphabets!")
                return redirect('checkout')
            
            if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                messages.error(request, "Please enter a valid email address.")
                return redirect('checkout')
            
            if not is_valid_phone(phone):
                messages.error(request, "Enter a valid 10-digit mobile number!")
                return redirect('checkout')
            
            if not is_valid_pincode(pincode):
                messages.error(request, "Enter a valid 6-digit pincode!")
                return redirect('checkout')
            
            if address.isdigit() :
                messages.error(request, "Enter a valid address")
                return redirect('checkout')
            
            new_address = Address()
            new_address.user=user
            new_address.fname=fname
            new_address.lname=lname
            new_address.email=email
            new_address.phone=phone
            new_address.address=address
            new_address.city=city
            new_address.state=state
            new_address.country=country
            new_address.pincode=pincode
            new_address.save()
            selected_address = new_address

        cart_items = Cart.objects.filter(user=request.user)
        cart_total_price = 0
        coupon_disc = 0
        cart_total_price = sum(item.total_cost for item in cart_items)
        coupon_exists = any(item.coupon for item in cart_items if item.coupon)
        if coupon_exists:
            for item in cart_items:
                if item.coupon:
                    cart_total_price -= item.coupon.discound_amount
                    coupon_disc = item.coupon.discound_amount
                    break
    
        new_order = Order()
        new_order.user = request.user
        new_order.fname = selected_address.fname
        new_order.lname = selected_address.lname
        new_order.country = selected_address.country
        new_order.city = selected_address.city
        new_order.state = selected_address.state
        new_order.pincode = selected_address.pincode
        new_order.phone = selected_address.phone
        new_order.email = selected_address.email
        new_order.total_price = cart_total_price
        new_order.coupon_discount_amount = coupon_disc
        new_order.payment_mode = request.POST.get('payment_mode')
        new_order.payment_id = request.POST.get('payment_id')

        trackno = 'kickoff' + str(random.randint(1111111, 9999999))
        while Order.objects.filter(tracking_no=trackno).exists():
            trackno = 'kickoff' + str(random.randint(1111111, 9999999))
        new_order.tracking_no = trackno

        if new_order.payment_mode == "paid by wallet":
            user_wallet = Wallet.objects.get(user=request.user)
            total_price = float(request.POST.get('total_price', 0))

            if user_wallet.wallet >= total_price:
                user_wallet.wallet -= total_price
                user_wallet.save()
            else:
                messages.warning(request, "Wallet balance is not sufficient.")
                return redirect('checkout')
            
        new_order.save()

        for item in cart_items:
            OrderItem.objects.create(
                order=new_order,
                product=item.product,
                price=item.product.price,
                quantity=item.product_qty,
                size=item.size
            )
            order_product = Product.objects.filter(id=item.product_id).first()
            size_variant = Variants.objects.filter(product=order_product, size=item.size).first()

            if size_variant:
                if size_variant.quantity >= item.product_qty:
                    size_variant.quantity -= item.product_qty
                    size_variant.save()
                    print("Quantity updated for product:", order_product.name)
                else:
                    print("Not enough stock for product:", order_product.name)
            else:
                print("Size variant not found for product:", order_product.name)
        
        Cart.objects.filter(user=request.user).delete()

        return render(request, 'cart/order_confirmation.html')

    return render(request, 'cart/checkout.html')



def order_confirmation(request) :
    return render(request, 'cart/order_confirmation.html')