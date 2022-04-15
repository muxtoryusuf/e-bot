from django.db import models
from django.db.models.signals import pre_save
from apps.core.utils.service import CategoryStatus
from apps.accounts.models import UserBot


class Category(models.Model):
    user = models.ForeignKey(UserBot, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    parent_category = models.ForeignKey('self', related_name='children', on_delete=models.SET_NULL, blank=True, null=True)
    path = models.TextField(null=True, blank=True)
    status = models.IntegerField(choices=CategoryStatus.choices, default=CategoryStatus.ACTIVE)

    def __str__(self):
        return f"{self.title}"

    class Meta:
        ordering = ['id']
        verbose_name_plural = "Categories"


class Product(models.Model):
    user = models.ForeignKey(UserBot, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="product/", null=True, blank=True)
    name = models.CharField(max_length=255)
    price = models.IntegerField(default=0)
    description = models.TextField(max_length=1500)

    def __str__(self):
        return f"{self.category.title} - {self.name}"


def pre_save_parent_category(sender, instance, **kwargs):
    instance.path = instance.title
    parent_category_obj = instance.parent_category
    while parent_category_obj is not None:
        instance.path = parent_category_obj.title + " > " + instance.path
        parent_category_obj = parent_category_obj.parent_category
pre_save.connect(pre_save_parent_category, sender=Category)