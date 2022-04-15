from .base import *

ALLOWED_HOSTS = ["*"]

DATABASES = {
    'default': {
        "ENGINE": os.environ.get("SQL_ENGINE", "django.db.backends.sqlite3"),
        "NAME": os.environ.get("SQL_DATABASE", os.path.join(BASE_DIR, "db.sqlite3")),
        "USER": os.environ.get("SQL_USER", "tb_user"),
        "PASSWORD": os.environ.get("SQL_PASSWORD", "tb_pass"),
        "HOST": os.environ.get("SQL_HOST", "tezdb"),
        "PORT": os.environ.get("SQL_PORT", "5432"),
    }
}



