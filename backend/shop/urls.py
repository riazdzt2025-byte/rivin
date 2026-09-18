from django.urls import path
from .api import (
    categories_api, products_api, product_detail_api, settings_api,
    create_order_api, order_detail_api, my_orders_api, review_api,
)

urlpatterns = [
    path('categories/', categories_api, name='api-categories'),
    path('products/', products_api, name='api-products'),
    path('products/<slug:sku>/', product_detail_api, name='api-product-detail'),
    path('settings/', settings_api, name='api-settings'),
    path('orders/', create_order_api, name='api-create-order'),
    path('orders/mine/', my_orders_api, name='api-my-orders'),
    path('orders/<str:order_no>/', order_detail_api, name='api-order-detail'),
    path('orders/<str:order_no>/review/', review_api, name='api-review'),
]
