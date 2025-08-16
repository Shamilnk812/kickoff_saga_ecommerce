from datetime import datetime, timedelta
import random

def generate_otp(request, minutes_valid=1):
    otp = str(random.randint(100000, 999999))
    request.session['otp'] = otp
    request.session['otp_valid_date'] = str(datetime.now() + timedelta(minutes=minutes_valid))
    return otp
