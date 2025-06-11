from django.urls import path
from . import views


from django.contrib.auth.views import (
    # LogoutView, 
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView,
    PasswordResetCompleteView
)


urlpatterns = [
    path('',views.home, name='home'),
    path('sign_up',views.sign_up, name='sign_up'),
    path('log_in',views.log_in, name='log_in'),
    path('log_out',views.log_out, name='log_out'),
    path('send_otp',views.send_otp, name='send_otp'),
    path('otp_verification',views.otp_verification, name='otp_verification'),
    path('resend_otp', views.resend_otp, name='resend_otp'),

    path('password-reset/', PasswordResetView.as_view(template_name='user/password_reset.html'),name='password-reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='user/password_reset_done.html'),name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='user/password_reset_confirm.html'),name='password_reset_confirm'),
    path('password-reset-complete/',PasswordResetCompleteView.as_view(template_name='user/password_reset_complete.html'),name='password_reset_complete'),



    path('show_single_product/<int:product_id>/',views.show_single_product, name='show_single_product'),
    path('store/', views.store, name='store'),
    path('search_products', views.search_products, name='search_products'),

    # path('user_profile' ,views.user_profile, name='user_profile')
    # path('home',views.home, name='home'),
    
]
