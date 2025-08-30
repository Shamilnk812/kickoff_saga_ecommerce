from django.urls import path
from . import views
from .forms import CustomPasswordResetForm, CustomSetPasswordForm


from django.contrib.auth.views import (
    # LogoutView, 
    PasswordResetView, 
    PasswordResetDoneView, 
    PasswordResetConfirmView,
    PasswordResetCompleteView
)


urlpatterns = [
    path('',views.home, name='home'),
    path('signup',views.sign_up, name='signup'),
    path('login',views.log_in, name='login'),
    path('logout',views.log_out, name='logout'),
    path('send-otp',views.send_otp, name='send-otp'),
    path('otp-verification',views.otp_verification, name='otp-verification'),
    path('resend-otp', views.resend_otp, name='resend-otp'),

    path('password-reset/', PasswordResetView.as_view(template_name='user/password_reset.html',  form_class=CustomPasswordResetForm),name='password-reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='user/password_reset_done.html'),name='password_reset_done'),
    path('password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='user/password_reset_confirm.html', form_class=CustomSetPasswordForm),name='password_reset_confirm'),
    path('password-reset-complete/',PasswordResetCompleteView.as_view(template_name='user/password_reset_complete.html'),name='password_reset_complete'),

    path('single-product/<int:product_id>/',views.show_single_product, name='single-product'),
    path('store/', views.store, name='store'),
    
]
