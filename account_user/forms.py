from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.models import User
import re
from admin_dash.constants import RESERVED_WORDS

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
    
    def validate_reserved(self, value, field_name):
        if value.lower() in RESERVED_WORDS:
            raise forms.ValidationError(f"{field_name} cannot be a this '{value}'. Please enter a valid one")
        return value
    

    # First name validation
    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name').strip()
        if not first_name:
            raise forms.ValidationError('First name is required')
        
        if " " in first_name:
            raise forms.ValidationError("Last name cannot contain spaces.")
        
        if len(first_name) < 2 or len(first_name) > 30:
            raise forms.ValidationError("First name must be between 2 and 30 characters.")
        
        if not first_name.isalpha():
            raise forms.ValidationError('First name must contain only letters.')
        return self.validate_reserved(first_name, "First Name")

    # Last name validation
    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name').strip()
        if not last_name:
            raise forms.ValidationError('Last name is required')
        if " " in last_name:
            raise forms.ValidationError("Last name cannot contain spaces.")
        
        if len(last_name) < 2 or len(last_name) > 30:
            raise forms.ValidationError("Last name must be between 2 and 30 characters.")
        
        if not last_name.isalpha():
            raise forms.ValidationError('Last name must contain only letters.')
        return self.validate_reserved(last_name, "Last Name")

    # Username validation
    def clean_username(self):
        username = self.cleaned_data.get('username').strip()
        if not username:
            raise forms.ValidationError('Username is required')
        
        if " " in username:
            raise forms.ValidationError("Username cannot contain spaces.")
        
        if len(username) < 2 or len(username) > 30:
            raise forms.ValidationError("Username must be between 2 and 30 characters.")

        # only allowed chars
        if not re.match(r'^[A-Za-z0-9_]+$', username):
            raise forms.ValidationError("Username can only contain letters, digits, and underscores.")

        # no consecutive underscores
        if "__" in username:
            raise forms.ValidationError("Username cannot contain consecutive underscores.")

        # no leading/trailing underscore
        if username.startswith("_") or username.endswith("_"):
            raise forms.ValidationError("Username cannot start or end with underscore.")

        # not only digits
        if username.isdigit():
            raise forms.ValidationError("Username cannot contain only digits.")

        if User.objects.filter(username__iexact=username).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('Username already exists.')
        return self.validate_reserved(username, "Username")

    # Email validation
    def clean_email(self):
        email = self.cleaned_data.get('email').strip()
        if not email:
            raise forms.ValidationError('Emial is required')
        if not re.match(r'^\S+@\S+\.\S+$', email):
            raise forms.ValidationError('Please enter a valid email address.')

        if User.objects.filter(email__iexact=email).exclude(id=self.instance.id).exists():
            raise forms.ValidationError('User with this email already exist..')
        return email



class PasswordInputWidget(forms.TextInput):
    input_type = 'password'


class ChangePasswordForm(forms.Form):
    current_password = forms.CharField(label='Current Password', widget=PasswordInputWidget(attrs={'class': 'form-control'}))
    new_password = forms.CharField(label='New Password', widget=PasswordInputWidget(attrs={'class': 'form-control'}))
    confirm_password = forms.CharField(label='Confirm New Password', widget=PasswordInputWidget(attrs={'class': 'form-control'}))

    def clean(self):
        cleaned_data = super().clean()
        current_password = cleaned_data.get("current_password")
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")
        
        
        if not current_password:
            self.add_error('current_password', 'Cureent password is required')
        
        # 1. Length check
        if new_password and len(new_password) < 8:
            self.add_error('new_password', 'Password must be at least 8 characters long.')

        if confirm_password and len(confirm_password) < 8:
            self.add_error('confirm_password', 'Password must be at least 8 characters long.')

        # 2. Password match check
        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', 'Passwords do not match.')

        # 3. At least one capital letter and one digit
        if new_password:
            if not re.search(r'[A-Z]', new_password):
                self.add_error('new_password', 'Password must contain at least one uppercase letter.')
            if not re.search(r'\d', new_password):
                self.add_error('new_password', 'Password must contain at least one digit.')

        return cleaned_data