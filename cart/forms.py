from django import forms
from account_user.models import Address

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['fname', 'lname', 'email', 'phone', 'address', 'city', 'state', 'country', 'pincode']



# class ShippingOptionForm(forms.Form):
#     shipping_options = forms.ChoiceField(
#         widget=forms.HiddenInput,
#         choices=[('0', 'Free Shipping'), ('10', 'Standard Shipping'), ('20', 'Express Shipping')],
#         initial='0',
#     )