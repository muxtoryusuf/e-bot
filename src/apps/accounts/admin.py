import requests
import time
from apps.core.utils.service import BASE_URL
from django.contrib import messages
from .models import User, UserBot, TGUser
from django.contrib import admin
from django import forms
from django.contrib.auth.forms import ReadOnlyPasswordHashField
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin


class UserChangeForm(forms.ModelForm):
    password = ReadOnlyPasswordHashField()

    class Meta:
        model = User
        fields = ('email', 'password', 'status', 'is_staff', 'is_superuser')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = UserChangeForm
    # readonly_fields = ("status",)
    filter_horizontal = ()
    list_display = ('id', 'phone_number', 'status', 'activated_date', 'created_at', 'updated_at')
    list_filter = ('status',)
    search_fields = ('phone_number', 'username', 'first_name', 'last_name', 'email')

    fieldsets = (
        (None, {
            'fields': (
                'username', 'first_name', 'last_name', 'email', 'phone_number', 'status', 'language')
        }),
        ('Important dates', {'fields': ('last_login', 'activated_date')}),
        ('Permissions', {'fields': ('is_superuser', 'is_staff')}),

    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 'first_name', 'last_name', 'email', 'phone_number',
                'activated_date', 'status', 'language', 'password1', 'password2',)
        }),
    )

    list_display_links = ('phone_number',)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if request.user.is_superuser:
            qs = qs.all()
        else:
            qs = qs.filter(id=user.id)
        return qs

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(UserBot)
class UserBotAdmin(admin.ModelAdmin):
    list_display = [
        "user",
        "bot_name",
        "bot_token",
        "created_at",
        "updated_at"
    ]
    list_filter = ("created_at",)
    list_display_links = ("bot_token", "user")
    search_fields = ('bot_name', 'user__phone_number')

    def save_model(self, request, obj, form, change):
        tg_url = "https://api.telegram.org/"
        url = f"{tg_url}bot{obj.bot_token}/setWebhook?url={BASE_URL}"
        set_url = f"{url}/bot/{obj.bot_name}"
        obj.user.id = form.data["user"]
        obj.save()
        if change:
            # print("ADMIN > IF > set_url", set_url)
            # https://api.telegram.org/bot5287768525:AAGtTCXFoefhLkjWuAXG7apf4tGpTJLSpgQ/setWebhook?url=https://e74b-185-139-137-18.ngrok.io&drop_pending_updates=true
            requests.get(url=f"{url}&drop_pending_updates=true")
            time.sleep(1)
            re = requests.get(url=set_url)
            if re.status_code == 200:
                messages.add_message(request, messages.SUCCESS, f'Webhook updated successfully for {obj.bot_name}')
            else:
                messages.add_message(request, messages.ERROR, f'Webhook updated failed for {obj.bot_name}')
        else:
            # print("ADMIN > Else > set_url",set_url)
            re = requests.get(url=set_url)
            if re.status_code == 200:
                messages.add_message(request, messages.SUCCESS, f'Webhook was set for {obj.bot_name}')
            else:
                messages.add_message(request, messages.ERROR, f'Webhook was unset for {obj.bot_name}')

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        user = request.user
        if request.user.is_superuser:
            qs = qs.all()
        else:
            qs = qs.filter(user_id=user.id)
        return qs

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser


@admin.register(TGUser)
class TGUserAdmin(admin.ModelAdmin):
    list_display = [
        "telegram_id",
        "first_name",
        "step",
        "username",
        "phone",
    ]
    list_filter = ("created_at",)
    list_display_links = ("telegram_id", "phone")
    search_fields = ('telegram_id', 'phone')

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser
