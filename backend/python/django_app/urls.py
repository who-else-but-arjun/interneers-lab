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
    category_products,
)
from django_app.adapters.ui_views import (
    inventory_dashboard,
    ui_product_delete,
    ui_export_products,
    ai_scenario_dashboard,
    ai_generate_products,
)

urlpatterns = [
    # HTML UI
    path("", inventory_dashboard, name="inventory_dashboard"),
    path("ui/products/<str:product_id>/delete/", ui_product_delete, name="ui_product_delete"),
    path("ui/products/export/", ui_export_products, name="ui_export_products"),
    
    # AI Scenario Selector (Week 6 Advanced)
    path("ai/scenarios/", ai_scenario_dashboard, name="ai_scenario_dashboard"),
    path("ai/generate/", ai_generate_products, name="ai_generate_products"),

    # JSON APIs
    path("admin/", admin.site.urls),
    path("hello/", hello_name),
    path("products/", product_list),
    path("products/bulk/", product_bulk_create),
    path("products/bulk/csv/", product_bulk_csv),
    path("products/<str:product_id>/", product_detail),
    path("products/<str:product_id>/category/", product_add_to_category),
    path("categories/", category_list),
    path("categories/<str:category_id>/", category_detail),
    path("categories/<str:category_id>/products/", category_products),
]
