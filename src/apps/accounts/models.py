from django.db import models
from apps.core.models import TimestampedModel
from apps.core.utils.service import UserStatus, LanguageType
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.utils.translation import ugettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, is_superuser=False):
        if not phone_number:
            raise ValueError('Users must have a phone number')
        user = self.model(phone_number=phone_number)
        if password is not None:
            user.set_password(password)
        user.status = UserStatus.INACTIVATE
        user.is_superuser = is_superuser
        user.save()
        return user

    def create_staffuser(self, phone_number, password):
        if not password:
            raise ValueError('staff/admins must have a password.')
        user = self.create_user(phone_number=phone_number, password=password)
        user.status = UserStatus.ACTIVATE
        user.is_active = True
        user.is_staff = True
        user.save()
        return user

    def create_superuser(self, phone_number, password):
        if not password:
            raise ValueError('superusers must have a password.')
        user = self.create_user(phone_number=phone_number, password=password, is_superuser=True)
        user.status = UserStatus.ACTIVATE
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.save()
        return user


class User(AbstractBaseUser, TimestampedModel):
    username = models.CharField(max_length=50, blank=True, null=True)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    email = models.EmailField(verbose_name='email address', blank=True, max_length=255, null=True)
    phone_number = models.CharField(max_length=50, db_index=True, unique=True)
    activated_date = models.DateTimeField(blank=True, null=True)
    token = models.CharField(max_length=255, blank=True, null=True)
    status = models.IntegerField(choices=UserStatus.choices, default=UserStatus.INACTIVATE)
    language = models.CharField(max_length=10, choices=LanguageType.choices, default=LanguageType.UZ)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = "user"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.phone_number}"

    def has_perm(self, perm, obj=None):
        return True  # does user have a specific permision, simple answer - yes

    def has_module_perms(self, app_label):
        return True  # does user have permission to view the app 'app_label'?


class UserBot(TimestampedModel):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    channel_id = models.CharField(max_length=255)
    bot_name = models.CharField(max_length=255)
    bot_token = models.CharField(max_length=255)
    tb_token = models.CharField(max_length=255)

    class Meta:
        db_table = "user_bot"
        verbose_name_plural = "User bots"

    def __str__(self):
        return f"{self.bot_name} / {self.user.phone_number}"


class TGUser(TimestampedModel):
    telegram_id = models.IntegerField(default=0)
    first_name = models.CharField(max_length=255, blank=True, null=True)
    last_name = models.CharField(max_length=255, blank=True, null=True)
    username = models.CharField(max_length=255, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    step = models.IntegerField(default=1)
    text = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "tg_user"
        verbose_name_plural = "Telegram Users"

    def __str__(self):
        return str(self.telegram_id)

