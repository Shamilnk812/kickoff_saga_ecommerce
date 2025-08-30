from django.urls import path
from . import views

urlpatterns = [
    path('',views.admin_log_in,name='admin-login'),
    path('admin-logout',views.admin_logout, name='admin-logout'),
    path('dashboard',views.dash_board, name='dashboard'),
    path('view-sales-reports', views.view_sales_reports, name='view-sales-reports'),
    path('download-pdf', views.download_pdf, name='download-pdf'),
    path('get-sales-data/<str:period>/', views.get_sales_data, name='get-sales-data'),

    path('user-management',views.user_management, name='user-management'),
    path('block-user/<int:user_id>/', views.block_user, name='block-user'),
    path('unblock-user/<int:user_id>/', views.unblock_user, name='unblock-user'),

    path('category-management',views.category_management, name='category-management'),
    path('add-category',views.add_category, name='add-category'),
    path('category-delete/<int:category_id>/', views.category_delete, name='category-delete'),
    path('update-category/<int:category_id>/',views.update_category, name='update-category'),
    
    path('brand-management',views.brand_management, name='brand-management'),
    path('add-brand', views.add_brand, name='add-brand'),
    path('update-brand/<int:brand_id>/', views.update_brand, name='update-brand'),
    path('block-brand/<str:brand_id>/', views.delete_brand, name='block-brand'),
    

    path('product-management', views.product_management, name='product-management'),
    path('add-product', views.add_product, name= 'add-product'),
    path('update-product/<int:product_id>/', views.update_product, name='update-product'),
    path('product-delete/<int:product_id>/', views.product_delete, name='product-delete'),
    path('publish-product/<int:product_id>/', views.publish_products, name='publish-product'),
    path('show-variants/<int:product_id>/',views.show_variants, name='show-variants'),
    path('add-image-product/<int:product_id>/', views.add_image_product, name='add-image-product'),
    path('delete-product-image/<int:img_id>/<int:product_id>/', views.delete_product_image, name='delete-product-image'),
    path('add-size-and-quantity/<int:product_id>/', views.add_size_and_quantity, name='add-size-and-quantity'),
    path('update-size-quantity/<int:variant_id>/', views.update_size_of_quantity, name='update-size-quantity'),
    path('delete-product-size/<int:variant_id>/<product_id>/', views.block_product_size, name='delete-product-size'),

    path('all-orders', views.all_orders, name='all-orders'),
    path('view-single-order/<str:ord_id>/', views.view_single_order, name='view-single-order'),
    path('view-all-order-items', views.view_all_order_items, name='view-all-order-items'),
    path('update-single-order-status/<str:ord_id>/', views.update_single_order_status, name='update-single-order-status'), 
    path('handle-cancel-single-order-item/<str:ord_id>/', views.cancel_single_order_by_admin, name='handle-cancel-single-order-item'),
    path('handle-cancel-all-order/<str:ord_id>/', views.cancel_all_order_by_admin, name='handle-cancel-all-order'),
    path('handle-return-order/<str:ord_id>/',views.manage_return_request, name='handle-return-order'),   

    path('view-coupons', views.view_coupons, name='view-coupons'),
    path('add-coupon', views.add_coupon, name='add-coupon'),
    path('delete-coupon/<str:c_id>/', views.delete_coupon, name='delete-coupon'),

    path('view-offers', views.view_offers, name='view-offers'),
    path('add-offer', views.add_offer, name='add-offer'),
    path('delete-offer/<str:off_id>/', views.delete_offer, name='delete-offer'),
    path('view-category-offers', views.view_category_offers, name='view-category-offers'),
    path('update-category-offer/<str:c_id>/', views.update_category_offer, name='update-category-offer'),
    path('remove-category-offer/<str:c_id>/',views.remove_category_offer, name='remove-category-offer'),
    path('view-product-offers', views.veiw_product_offers, name='view-product-offers'),
    path('update-product-offer/<str:p_id>/', views.update_product_offer, name='update-product-offer'),
    path('remove-product-offer/<str:p_id>/',views.remove_product_offer, name='remove-product-offer'),

    path('banner-management', views.banner_management, name='banner-management'),
    path('add-banner-image', views.add_banner_image, name='add-banner-image'),
    path('delete-banner/<str:b_id>/', views.delete_banner, name='delete-banner'),
]

