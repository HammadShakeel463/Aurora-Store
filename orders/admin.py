from django.contrib import admin

from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "price", "quantity"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["reference", "first_name", "last_name", "email", "status", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["reference", "email", "last_name"]
    inlines = [OrderItemInline]
