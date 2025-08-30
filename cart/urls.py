from django.urls import path
from . import views

urlpatterns = [
  
    path('view_cart/', views.view_cart, name='view_cart'),
    path('add/', views.add_to_cart, name='cart-add'),
    path('remove/<int:cart_id>/items/', views.remove_cart_item, name='cart-item-remove'),
    path('update/', views.update_cart, name='cart-update'),

    path('wishlist/', views.view_wishlist, name='wishlist'),
    path('wishlist/add/', views.add_to_wishlist, name='wishlist-add'),
    path('wishlist/items/<str:p_id>/remove/', views.remove_wishlist_product, name='wishlist-item-remove'),

    path('coupons/remove/', views.remove_coupon, name='coupon-remove'),
    path('checkout', views.check_out, name='checkout'),
    path('wallet-balance', views.check_wallet_balance, name='check-wallet-balance'),
    path('shipping-update', views.update_shipping, name='shipping-update'),
    path('place_order', views.place_order, name='place_order'),

    path('order-confirmation', views.order_confirmation, name='order-confirmation'),
]
