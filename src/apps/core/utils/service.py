from django.db import models
from geopy.geocoders import Nominatim
from django.db.models import F, Q
LOCATOR = Nominatim(user_agent="weboasis9002@gmail.com", timeout=3)

# https://gobazar.magician.casa/
BASE_URL = "https://gobazar.magician.casa"


class UserStatus(models.IntegerChoices):
    INACTIVATE = 1
    ACTIVATE = 2
    DELETED = 4


class LanguageType(models.TextChoices):
    UZ = "UZ", "uz"
    EN = "EN", "en"
    RU = "RU", "ru"


class GlobalStatus(models.IntegerChoices):
    ACTIVE = 1
    INACTIVE = 2
    DELETED = 4


class CategoryStatus(models.IntegerChoices):
    ACTIVE = 1
    INACTIVE = 2
    DELETED = 4


class OrderStatus(models.IntegerChoices):
    NEW = 1
    PROCESSING = 2
    FINISHED = 4
    CANCEL = 8


LANGUAGE_DATA = {
    "uz": {"hello": "Salom", "back": "orqaga"},
    "oz": {"hello": "Салом", "back": "ортга"},
    "ru": {"hello": "Привет", "back": "️назад"},
}


class GeoAPI:
    def __init__(self, location: tuple):
        self.location = location

    def get_address(self):
        """
        > location_city: Given coordinate city = Tashkent
        > address: raw address = Tashkent Region, 160100, Uzbekistan
        """
        try:
            location = LOCATOR.reverse(self.location)
            address = location.raw['address']
            city = address.get('city', None)
            state = address.get('state', None)
            region = address.get('region', None)
            print(f"Location administration ... \n{address}\n1-{city}\n2-{state}\n3-{region}")
            if city:
                location_city = city
            elif state:
                location_city = state.split()[0]
            elif region:
                location_city = region.split()[0]
            else:
                location_city = "None None None"
            return location_city, location
        except Exception as e:
            print("Exc....", e.args)
            return "None None None", e.args
