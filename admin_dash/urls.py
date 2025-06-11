from django.urls import path
from . import views

urlpatterns = [
    path('',views.admin_log_in,name='admin_log_in'),
    path('admin_logout',views.admin_logout, name='admin_logout'),
    path('dash_board',views.dash_board, name='dash_board'),
    path('view_sales_reports', views.view_sales_reports, name='view_sales_reports'),
    path('download_pdf', views.download_pdf, name='download_pdf'),

    # urls.py
    path('get_sales_data/<str:period>/', views.get_sales_data, name='get_sales_data'),


    # path('get_order_item_data', views.get_order_item_data, name='get_order_item_data'),

    path('user_management',views.user_management, name='user_management'),
    path('search_user', views.search_user, name='search_user'),
    path('block-unblock-user/<int:user_id>/', views.block_unblock_user, name='block_unblock_user'),
    path('category_management',views.category_management, name='category_management'),
    path('add_category',views.add_category, name='add_category'),
    path('category_delete/<int:category_id>/', views.category_delete, name='category_delete'),
    path('edit_category/<int:category_id>/', views.edit_category, name='edit_category'),
    path('update_category/<int:category_id>/',views.update_category, name='update_category'),
    
    path('brand_management',views.brand_management, name='brand_management'),
    path('add_brand', views.add_brand, name='add_brand'),
    path('edit_brand/<int:brand_id>/', views.edit_brand, name='edit_brand'),
    path('update_brand/<int:brand_id>/', views.update_brand, name='update_brand'),
    path('delete_brand/<str:brand_id>/', views.delete_brand, name='delete_brand'),
    

    path('product_management', views.product_management, name='product_management'),
    path('add_product', views.add_product, name= 'add_product'),
    path('edit_product/<int:product_id>/', views.edit_product, name='edit_product'),
    path('update_product/<int:product_id>/', views.update_product, name='update_product'),
    path('product_delete/<int:product_id>/', views.product_delete, name='product_delete'),
    path('show_variants/<int:product_id>/',views.show_variants, name='show_variants'),
    path('add_image_product/<int:product_id>/', views.add_image_product, name='add_image_product'),
    path('delete_product_image/<int:img_id>/', views.delete_product_image, name='delete_product_image'),
    path('add_size_and_quantity/<int:product_id>/', views.add_size_and_quantity, name='add_size_and_quantity'),
    path('delete_product_size/<int:variant_id>/', views.delete_product_size, name='delete_product_size'),

    path('all_orders', views.all_orders, name='all_orders'),
    path('view_single_order/<str:ord_id>/', views.view_single_order, name='view_single_order'),
    path('edit_order_status/<str:ord_id>/', views.edit_order_status, name='edit_order_status'),
    path('update_order_status/<str:ord_id>/', views.update_order_status, name='update_order_status'),
    path('delete_order_admin/<str:ord_id>/', views.delete_order_admin, name='delete_order_admin'),

    path('view_coupons', views.view_coupons, name='view_coupons'),
    path('add_coupon', views.add_coupon, name='add_coupon'),
    path('delete_coupon/<str:c_id>/', views.delete_coupon, name='delete_coupon'),

    path('view_offers', views.view_offers, name='view_offers'),
    path('add_offer', views.add_offer, name='add_offer'),
    path('delete_offer/<str:off_id>/', views.delete_offer, name='delete_offer'),
    path('view_category_offers', views.view_category_offers, name='view_category_offers'),
    path('offers_for_category/<str:c_id>/', views.offers_for_category, name='offers_for_category'),
    path('update_category_offer/<str:c_id>/', views.update_category_offer, name='update_category_offer'),
    path('remove_category_offer/<str:c_id>/',views.remove_category_offer, name='remove_category_offer'),
    path('viwe_product_offers', views.veiw_product_offers, name='viwe_product_offers'),
    path('offers_for_product/<str:p_id>/', views.offers_for_product, name='offers_for_product'),
    path('update_product_offer/<str:p_id>/', views.update_product_offer, name='update_product_offer'),
    path('remove_product_offer/<str:p_id>/',views.remove_product_offer, name='remove_product_offer'),

    path('banner_management', views.banner_management, name='banner_management'),
    path('add_banner_image', views.add_banner_image, name='add_banner_image'),
    path('delete_banner/<str:b_id>/', views.delete_banner, name='delete_banner'),
]

