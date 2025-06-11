# Kickoff Saga Ecommerce

Kickoff Saga is a full-featured ecommerce web application built for football-related products. It includes user-friendly features like OTP-based registration, product browsing with zoom and size selection, wishlist, cart, secure payments via Razorpay, order tracking, invoice generation, and much more.

##  Features

### User Side

- OTP-based user registration and login
- Browse football-related products
- Product zoom functionality
- Select size and quantity
- Add to wishlist
- Add to cart
- Apply offers and coupons
- Secure payments with Razorpay
- Order tracking by status
- Cancel orders
- Download invoice

### 🛠️ Admin Panel

- User management (view, block/unblock, delete users)
- Brand management (add, update, delete brands)
- Product management (CRUD operations on products)
- Category management (add, edit, delete categories)
- Coupon management
- Offer management for products and categories
- View and analyze sales data
- Generate downloadable sales reports

## Tech Stack

- Backend: Django (MVT architecture)
- Database: PostgreSQL
- OTP: PyOTP
- Frontend: HTML, CSS, Bootstrap

## 🛠️ Project Setup

### Clone the repository

```bash
https://github.com/Shamilnk812/kickoff-ecommerce.git
```

### Navigate to root directory

```bash
cd kick_off
```

### Create and activate a virtual environment

```bash
python -m venv venv
source venv/bin/activate #linux
venv/scripts/activate  # windows
```

### Install the dependencies

```bash
pip install -r requirements.txt
```

### Create a .env file in the root directory and add your environment variables

```bash
SECRET_KEY=your-django-secret-key
DEBUG=True


EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_USE_TLS=True
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=dummyemail@example.com
EMAIL_HOST_PASSWORD=dummypassword123

DB_NAME=kickoff_saga_db
DB_USER=kickoff_saga_user
DB_PASSWORD=strong_dummy_password
DB_HOST=localhost
DB_PORT=5432
```

### Apply migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Run the development server using Daphne

```bash
python manage.py runserver
```

- Open your browser and go to http://localhost:8000
