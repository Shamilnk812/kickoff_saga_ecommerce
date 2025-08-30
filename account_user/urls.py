from django.urls import path
from . import views

urlpatterns = [
    path('account-details/', views.account_details, name='account-details'),
    path('orders/', views.user_orders, name='orders'),
    path('orders/<str:order_id>/', views.view_order, name='order-detail'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='order-cancel'),
    path('orders/<int:order_id>/cancel-item/', views.cancel_single_item, name='order-cancel-item'),
    path('orders/<int:order_id>/return-item/', views.return_single_item, name='order-return-item'),
    path('orders/<int:order_id>/items/<int:order_item_id>/invoice/', views.generate_invoice, name='order-invoice'),

    path('addresses/', views.user_address, name='addresses'),
    path('addresses/<str:ad_id>/edit/', views.edit_address, name='address-edit'),
    path('addresses/<str:ad_id>/update/', views.update_address, name='address-update'),
    path('addresses/<str:ad_id>/delete/', views.delete_user_address, name='address-delete'),

    path('wallet', views.user_wallet, name='wallet'),
    path('transactions', views.Transaction_histroy, name='transactions'),
    
]
