import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "stripe_shop.settings")
application = get_wsgi_application()
