from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("cart/", include("cart.urls")),
    path("orders/", include("orders.urls")),
    path("", include("catalog.urls")),
]
