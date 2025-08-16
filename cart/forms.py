from django import forms
from account_user.models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['fname', 'lname', 'email', 'phone', 'address', 'city', 'state', 'country', 'pincode']


