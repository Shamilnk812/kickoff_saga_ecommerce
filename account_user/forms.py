from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User

class UserUpdateForm(UserChangeForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control ','readonly': 'readonly'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class PasswordInputWidget(forms.TextInput):
    input_type = 'password'


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(label='Current Password', widget=PasswordInputWidget(attrs={'class': 'form-control'}))
    new_password = forms.CharField(label='New Password', widget=PasswordInputWidget(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(label='Confirm New Password', widget=PasswordInputWidget(attrs={'class': 'form-control'}))