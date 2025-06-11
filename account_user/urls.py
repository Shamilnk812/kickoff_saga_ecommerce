from django.urls import path
from . import views

urlpatterns = [
    # path('user_profile', views.user_account , name='user_profile'),
    path('account_details/', views.account_details, name='account_details'),
    path('user_orders', views.user_orders, name='user_orders'),
    path('user_wallet', views.user_wallet, name='user_wallet'),
    path('user_address', views.user_address, name='user_address'),
    path('edit_address/<str:ad_id>/', views.edit_address, name='edit_address'),
    path('update_address/<str:ad_id>/', views.update_address, name='update_address'),
    path('delete_user_address/<str:ad_id>/',views.delete_user_address, name='delete_user_address'),
    path('view_order/<str:t_no>/', views.view_order, name='view_order'),
    path('cancel_order/<str:t_no>/', views.cancel_order, name='cancel_order'),
    path('download_invoice/<str:order_id>/', views.generate_invoice, name='download_invoice'),
    
]
