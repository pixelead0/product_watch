"""
WSGI config for product_watch project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "product_watch.settings")

application = get_wsgi_application()
