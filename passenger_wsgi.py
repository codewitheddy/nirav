"""
Passenger WSGI file for cPanel deployment
This file is required by cPanel's Python application setup
"""
import os
import sys

# Add your project directory to the sys.path
project_home = os.path.dirname(os.path.abspath(__file__))
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set environment variable for Django settings module
os.environ['DJANGO_SETTINGS_MODULE'] = 'jewellery_site.settings'

# Import Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
