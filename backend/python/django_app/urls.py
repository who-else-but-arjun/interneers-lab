from django.contrib import admin
from django.urls import path
from django_app.adapters.hello_views import hello_name
from django_app.adapters.product_views import (
    product_list,
    product_detail,
    product_bulk_create,
    product_bulk_csv,
    product_add_to_category,
)
from django_app.adapters.category_views import (
    category_list,
    category_detail,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("hello/", hello_name),
    path("products/", product_list),
    path("products/bulk/", product_bulk_create),
    path("products/bulkcsv/", product_bulk_csv),
    path("products/<str:product_id>/", product_detail),
    path("products/<str:product_id>/category/", product_add_to_category),
    path("categories/", category_list),
    path("categories/<str:category_id>/", category_detail),
]
