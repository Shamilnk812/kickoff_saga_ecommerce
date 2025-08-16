from django.urls import path
from . import views

urlpatterns = [
    path('account_details/', views.account_details, name='account_details'),
    path('user_orders', views.user_orders, name='user_orders'),
    path('user_wallet', views.user_wallet, name='user_wallet'),
    path('user_address', views.user_address, name='user_address'),
    path('edit_address/<str:ad_id>/', views.edit_address, name='edit_address'),
    path('update_address/<str:ad_id>/', views.update_address, name='update_address'),
    path('delete_user_address/<str:ad_id>/',views.delete_user_address, name='delete_user_address'),
    path('view_order/<str:order_id>/', views.view_order, name='view_order'),
    path('cancel_order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('cancel_single_item/<int:order_id>/', views.cancel_single_item, name='cancel_single_item'),
    path('return_single_item/<int:order_id>/', views.return_single_item, name='return_single_item'),
    path('download_invoice/<int:order_id>/<int:order_item_id>/', views.generate_invoice, name='download_invoice'),
    path('view_payment_history', views.Transaction_histroy, name='view_payment_history'),
    
]
