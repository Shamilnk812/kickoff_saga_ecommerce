from .models import Cart,Wishlist

def cart_count(request):
    cart_item_count = 0
    if request.user.is_authenticated:
        cart_item_count = Cart.objects.filter(user=request.user).count()

    return {'cart_item_count': cart_item_count}


def wishlist_count(request) :
    wishlist_item_count = 0 
    if request.user.is_authenticated :
        wishlist_item_count = Wishlist.objects.filter(user=request.user).count()

    return {'wishlist_item_count': wishlist_item_count}    