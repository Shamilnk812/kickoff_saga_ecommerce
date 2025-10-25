import random
from decimal import Decimal, ROUND_HALF_UP
from django.contrib import messages
from account_user.validators import *
from account_user.models import *
from .models import *




def handle_address_submission(request):
    user = request.user
    address_id = request.POST.get('address_id')

    if address_id:
        try:
            return Address.objects.get(id=address_id, user=user)
        except Address.DoesNotExist:
            messages.error(request, "Selected address is invalid.")
            return None

    data = {
        'fname': request.POST.get('fname', '').strip(),
        'lname': request.POST.get('lname', '').strip(),
        'email': request.POST.get('email', '').strip(),
        'phone': request.POST.get('phone', '').strip(),
        'address': request.POST.get('address', '').strip(),
        'city': request.POST.get('city', '').strip(),
        'state': request.POST.get('state', '').strip(),
        'country': request.POST.get('country', '').strip(),
        'pincode': request.POST.get('pincode', '').strip()
    }

    if not all(data.values()):
        messages.error(request, "Please fill in all required address fields.")
        return None

    if not all(map(is_alpha, [data['fname'], data['lname'], data['city'], data['state'], data['country']])):
        messages.error(request, "Name, city, state, and country must contain only alphabets.")
        return None

    if not is_valid_phone(data['phone']) :
        messages.error(request, "Invalid phone number")
        return None
    
    if not is_valid_pincode(data['pincode']):
        messages.error(request, "Invalid pincode.")
        return None

    if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', data['email']):
        messages.error(request, "Invalid email format.")
        return None

    address = Address(user=user, **data)
    address.save()
    return address



def apply_coupon(code, total_price):
    coupon = Coupon.objects.filter(coupon_code=code, is_active=True).first()
    if coupon and total_price >= coupon.minimum_amount:
        return coupon.calculate_discount(total_price), coupon
    return 0, None



def create_order(user, address, total_price, post_data, coupon_discount, offer_saved_amount, shipping_type, shipping_amount):
    print('createeee order total price', total_price)
    order = Order(
        user=user,
        fname=address.fname,
        lname=address.lname,
        email=address.email,
        phone=address.phone,
        address=address.address,
        city=address.city,
        state=address.state,
        country=address.country,
        pincode=address.pincode,
        total_price=total_price,
        coupon_discount_amount=coupon_discount,
        offer_discount_amount=offer_saved_amount,
        payment_mode=post_data.get('payment_mode'),
        payment_id=post_data.get('payment_id'),
        tracking_no=generate_tracking_number(),
        shipping_type=shipping_type,
        shipping_amount=shipping_amount
    )
    order.save()
    return order


def generate_tracking_number():
    while True:
        track = 'kickoff' + str(random.randint(1111111, 9999999))
        if not Order.objects.filter(tracking_no=track).exists():
            print('traaaaaack')
            return track


def create_order_item(order, cart_item, total_cart_amount, coupon_discount):
    product = cart_item.product
    saved_amount = Decimal(str(product.offer_save_amount())) * Decimal(cart_item.product_qty)
    after_offer_discount = Decimal(str(product.discounted_price()))
    total_per_item = after_offer_discount * Decimal(cart_item.product_qty)
    discount_share = (total_per_item / Decimal(str(total_cart_amount))) * Decimal(str(coupon_discount))
    final_price = total_per_item - discount_share
    final_price_for_each_item = final_price / Decimal(cart_item.product_qty)

    OrderItem.objects.create(
        order=order,
        product=product,
        price=float(final_price_for_each_item), 
        quantity=cart_item.product_qty,
        size=cart_item.size,
        offer_saved_amount=float(saved_amount)
    )
    
    variant = Variants.objects.select_for_update().filter(
        product=cart_item.product, size=cart_item.size
    ).first()
    if variant:
        variant.quantity -= cart_item.product_qty
        variant.save()


# Create transaction history
def create_payment(user, order,transaction_type, amount, payment_mode, description ):
    
    PaymentHistory.objects.create(
        user=user,
        order=order,
        transaction_type=transaction_type,
        amount=amount,
        status='completed',
        payment_mode=payment_mode,
        description=description
    )