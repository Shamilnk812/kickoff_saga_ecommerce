import re

def is_alpha(value):
    return value.isalpha()

def is_valid_phone(phone):
    if not re.match(r'^[6-9]\d{9}$', phone):
        return False
    if phone in ['0000000000', '1111111111', '2222222222']:
        return False
    return True

def is_valid_pincode(pincode):
    return re.match(r'^[1-9][0-9]{5}$', pincode) is not None
