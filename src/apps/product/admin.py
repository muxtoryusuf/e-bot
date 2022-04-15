from django.contrib import admin
from .models import Product, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "title",
        "parent_category",
        "path"
    ]
    list_filter = ("parent_category", )
    list_display_links = ("title", )
    search_fields = ('title', )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser:
            qs = qs.all()
        else:
            qs = qs.filter(user__user_id=user.id)
        return qs


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):

    list_display = [
        "user",
        "category",
        "name",
        "price"
    ]
    list_filter = ("category", )
    list_display_links = ("name", "user")
    search_fields = ('name', )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if user.is_superuser:
            qs = qs.all()
        else:
            qs = qs.filter(user__user_id=user.id)
        return qs

