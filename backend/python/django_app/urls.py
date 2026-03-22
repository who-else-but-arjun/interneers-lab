from django.contrib import admin
from django.urls import path
from django_app.adapters.hello_views import hello_name

urlpatterns = [
    path("admin/", admin.site.urls),
    path("hello/", hello_name),
]
