from django.db import models
from django.db.models.signals import post_save
import requests
import json
from apps.accounts.models import TGUser, UserBot
from apps.product.models import Product
from apps.core.models import TimestampedModel
from apps.core.utils.service import OrderStatus, F


class Order(TimestampedModel):
    user_bot = models.ForeignKey(UserBot, on_delete=models.CASCADE)
    tg_user = models.ForeignKey(TGUser, on_delete=models.CASCADE)
    status = models.IntegerField(choices=OrderStatus.choices, default=OrderStatus.NEW)
    total = models.IntegerField(default=0)
    latitude = models.CharField(max_length=200, blank=True, null=True)
    longitude = models.CharField(max_length=200, blank=True, null=True)
    phone = models.CharField(max_length=255, blank=True, null=True)
    region = models.CharField(max_length=255, blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = "order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"{self.tg_user.telegram_id} / {self.tg_user.username}"

    def tg_user_name(self):
        return self.tg_user.username

    def parse_region_name(self):
        data = {
            "Тошкент шахри": "TAS",
            "Тошкент вилояти": "TOS",
            "Қорақалпоғистон": "KAR",
            "Андижон": "AND",
            "Бухоро": "BUK",
            "Жиззах": "JIZ",
            "Қашқадарё": "QAS",
            "Навоий": "NAV",
            "Наманган": "NAM",
            "Самарқанд": "SAM",
            "Сурхондарё": "SUR",
            "Сирдарё": "SIR",
            "Фарғона": "FER",
            "Хоразм": "XOR",
            "tas": "TAS",
            "tos": "TOS",
            "qor": "KAR",
            "kar": "KAR",
            "and": "AND",
            "bux": "BUK",
            "buk": "BUK",
            "jiz": "JIZ",
            "dji": "JIZ",
            "qas": "QAS",
            "kas": "QAS",
            "nav": "NAV",
            "nam": "NAM",
            "sam": "SAM",
            "sur": "SUR",
            "sir": "SIR",
            "syr": "SIR",
            "far": "FER",
            "fer": "FER",
            "xor": "XOR",
            "kho": "XOR"
        }
        region = data.get(self.region, None)
        by_prefix = data.get(self.region.lower()[:3], None)
        if region:
            return region
        if by_prefix:
            return by_prefix
        else:
            return None

    def create_tezbor_parcel(self):
        city = self.parse_region_name()
        if self.region and len(self.region.split()) == 1:
            prod_url = "https://delivery.uz/api/orders/v1/create-order"
            data = {
                "receiver_name": self.tg_user.first_name,
                "receiver_phone": self.phone,
                "description": f"#{self.id}",
                "from": None,
                "to": {
                    "name": self.tg_user.first_name or self.tg_user.username,
                    "address1": self.address,
                    "address2": self.address,
                    "latitude": self.latitude,
                    "longitude": self.longitude,
                    "city": city,
                    "full_name": f"{self.tg_user.first_name} {self.tg_user.last_name}",
                    "phone_number": self.phone,
                    "type": 1
                },
                "parcel_size": {"weight": 1.0, "width": 10, "height": 10, "length": 10},
                "delivery_option": 1,
                "images": None
            }
            headers = {"content-type": "application/json", "Authorization": f"Token {self.user_bot.tb_token}"}
            re = requests.post(url=prod_url, json=data, headers=headers)
            if re.status_code == requests.codes.ok:
                return True
            else:
                return False


class OrderProduct(TimestampedModel):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)

    class Meta:
        db_table = "order_item"
        verbose_name_plural = "Order products"

    def __str__(self):
        return f"{self.product.image}"


def post_save_oder(sender, instance: OrderProduct, created, *args, **kwargs):
    if created:
        order = instance.order
        order.total = instance.quantity * instance.product.price
        order.save()
post_save.connect(post_save_oder, sender=OrderProduct)

