from django.contrib import admin
from .models import OrderProduct, Order


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "user_bot",
        "tg_user",
        "tg_user_name",
        "status",
        "total",
    ]
    list_filter = ("created_at", "status")
    list_display_links = ("user_bot", "tg_user")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser:
            qs = qs.all()
        else:
            qs = qs.filter(user_bot__user_id=user.id)
        return qs

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

@admin.register(OrderProduct)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "order",
        "product",
        "quantity"
    ]
    list_filter = ("created_at",)
    list_display_links = ("order", "product")

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser:
            qs = qs.all()
        else:
            qs = qs.filter(order__user_bot__user_id=user.id)
        return qs

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser
