from django.core.paginator import Paginator
from  django.core.mail import send_mail
from django.conf import settings
from django.db.models import F, Sum
from datetime import datetime, timedelta
from django.utils import timezone
from cart.models import OrderItem
import calendar
# Utility function for paginatoin 
def paginate_queryset(queryset, request, per_page=10):
    paginator = Paginator(queryset, per_page)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)


# Send user account block email
def send_block_email(user_email, username, reason):
    subject = "Account Blocked Notification"
    message = f"""
        Hi {username},
        Your account has been blocked by the admin for the following reason:
        "{reason}"
        If you have any questions, please contact us.

        Regards,
        Kickoff Saga
        """
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


# Send user account unblock email
def send_account_unblock_email(user_email, username):
    subject = 'Your Kickoff Saga Account Has Been Unblocked'
    message = f"""
        Hello {username},

        We are pleased to inform you that your Kickoff Saga account has been unblocked.
        You can now log in and continue using all features of our platform.

        Thank you,
        Kickoff Saga Support Team
        """
    from_email = settings.DEFAULT_FROM_EMAIL
    recipient_list = [user_email]

    send_mail(subject, message, from_email, recipient_list, fail_silently=False)


    

def get_filtered_orders(time_range=None, start_date_input=None, end_date_input=None, status=None):
    """
    Returns queryset of orders filtered by date range or time range.
    """
    today = timezone.now().date()

    # Default time range
    if not time_range:
        time_range = 'all'

    # Default start date from dropdown
    if time_range == 'day':
        start_date = today
    elif time_range == 'week':
        start_date = today - timedelta(weeks=1)
    elif time_range == 'month':
        start_date = today - timedelta(days=30)
    elif time_range == 'year':
        start_date = today - timedelta(days=365)
    elif time_range == 'all':
        start_date = today - timedelta(days=365)
    else:
        start_date = today

    # If user provided start & end date in inputs, override the dropdown range
    if start_date_input and end_date_input:
        start_date_obj = datetime.strptime(start_date_input, "%Y-%m-%d").date()
        end_date_obj = datetime.strptime(end_date_input, "%Y-%m-%d").date()

        # Validation
        if start_date_obj > today or end_date_obj > today:
            return None, "Dates cannot be in the future."
        if start_date_obj > end_date_obj:
            return None, "Start date cannot be after end date."

        start_date = start_date_obj
        end_date = end_date_obj

        orders = OrderItem.objects.filter(
            status=status,
            created_at__gte=start_date,
            created_at__lte=end_date
        ).select_related('order', 'product').order_by('-id')

    else:
        
        if status:
            orders = OrderItem.objects.filter(
                status=status,
                created_at__gte=start_date
            ).select_related('order', 'product').order_by('-id')
        else:
            orders = OrderItem.objects.filter(
                created_at__gte=start_date
            ).select_related('order', 'product').order_by('-id')


    total_amount = orders.aggregate(total=Sum(F('price') * F('quantity')))['total'] or 0
    return orders, total_amount



def get_period_label(period):
    
    today = timezone.now().date()

    if period == 'month':
        start_date = today 
        return f"{calendar.month_name[today.month]} {start_date.year}"
    
    elif period == 'week':
        week_start = today - timedelta(weeks=1)
        week_end = today 
        return f"{week_start.strftime('%d %b %Y')} - {week_end.strftime('%d %b %Y')}"
    
    elif period == 'year':
        return str(start_date.year)
    
    elif period == 'day':
        start_date = today
        return start_date.strftime('%d %b %Y')
    
    else:
        return None
