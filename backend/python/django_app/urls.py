from django.contrib import admin
from django.urls import path
from django_app.adapters.hello_views import hello_name
from django_app.adapters.product_views import product_list, product_detail, product_bulk_create

urlpatterns = [
    path("admin/", admin.site.urls),
    path("hello/", hello_name),
    path("products/", product_list),
    path("products/bulk/", product_bulk_create),
    path("products/<str:product_id>/", product_detail),
]
