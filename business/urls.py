from django.urls import path
from . import views


urlpatterns = [
    path('shops/', views.shop_list,   name='shop_list'),
    path('shops/create/', views.shop_create, name='shop_create'),
    path('shops/<uuid:shop_id>/', views.shop_detail, name='shop_detail'),
    path('shops/<uuid:shop_id>/update/',
         views.shop_update, name='shop_update'),
    path('shops/<uuid:shop_id>/delete/',
         views.shop_delete, name='shop_delete'),

    path('products/', views.product_list,   name='product_list'),
    path('products/create/', views.product_create, name='product_create'),
    path('products/<uuid:product_id>/',
         views.product_detail, name='product_detail'),
    path('products/<uuid:product_id>/update/',
         views.product_update, name='product_update'),
    path('products/<uuid:product_id>/delete/',
         views.product_delete, name='product_delete'),

    path('orders/', views.order_list, name='order_list'),
    path('orders/create/', views.order_create, name='order_create'),
    path('orders/<uuid:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<uuid:order_id>/status/',
         views.order_update_status, name='order_update_status'),

    path('reviews/', views.review_list,   name='review_list'),
    path('reviews/create/', views.review_create, name='review_create'),
    path('reviews/<uuid:review_id>/',
         views.review_detail, name='review_detail'),
    path('reviews/<uuid:review_id>/delete/',
         views.review_delete, name='review_delete'),
]
