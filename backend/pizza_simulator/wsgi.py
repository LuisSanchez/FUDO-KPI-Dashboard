"""
WSGI config for pizza_simulator project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "pizza_simulator.settings")

application = get_wsgi_application()
