from django.contrib.auth.forms import PasswordResetForm, SetPasswordForm
from django.contrib.auth.models import User
from django import forms 
import re
from admin_dash.constants import RESERVED_WORDS


class UserRegistrationForm(forms.ModelForm):
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter password'}),
        label="Password"
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm password'}),
        label="Confirm Password"
    )

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First ame'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}),
            'username': forms.TextInput(attrs={'class': 'form-control','placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        }

    
    def validate_reserved(self, value, field_name):
        if value.lower() in RESERVED_WORDS:
            raise forms.ValidationError(f"{field_name} cannot be a this '{value}'. Please enter a valid one")
        return value
    
    def clean_first_name(self):
        first_name = self.cleaned_data['first_name'].strip()
        if not first_name:
            raise forms.ValidationError("First name is required")
        
        if " " in first_name:
            raise forms.ValidationError("First name cannot contain spaces.")
        
        if len(first_name) < 2 or len(first_name) > 30:
            raise forms.ValidationError("First name must be between 2 and 30 characters.")
        
        if not first_name.isalpha():
            raise forms.ValidationError("First name should only contain alphabetic characters.")
        return self.validate_reserved(first_name, 'First Name')

    def clean_last_name(self):
        last_name = self.cleaned_data['last_name'].strip()
        if not last_name:
            raise forms.ValidationError("Last name is required")
        
        if " " in last_name:
            raise forms.ValidationError("Last name cannot contain spaces.")
        
        if len(last_name) < 2 or len(last_name) > 30:
            raise forms.ValidationError("Last name must be between 2 and 30 characters.")
        
        if not last_name.isalpha():
            raise forms.ValidationError("Last name should only contain alphabetic characters.")
        return self.validate_reserved(last_name, "Last name")

    def clean_username(self):
        username = self.cleaned_data['username'].strip()
        if not username:
            raise forms.ValidationError("Username is required")

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

        if username.isdigit():
            raise forms.ValidationError("Username cannot contain only digits.")

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("Username is already taken.")
        return self.validate_reserved(username, "Username")

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            raise forms.ValidationError("Enter a valid email address.")
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("User with this email already exist.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match.")
            if len(password1) < 8:
                raise forms.ValidationError("Password must be at least 8 characters long.")
            if not any(char.isupper() for char in password1):
                raise forms.ValidationError("Password must contain at least one uppercase letter.")
            if not any(char.isdigit() for char in password1):
                raise forms.ValidationError("Password must contain at least one digit.")
        return cleaned_data



# For the reset password 
class CustomPasswordResetForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label
            })


# For the confirm password setup
class CustomSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs.update({
                'class': 'form-control',
                'placeholder': field.label
            })

