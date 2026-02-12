"""
Pytest configuration for Django projects.

This file configures pytest-django to use the correct Django settings module.
"""

import os
import django
from django.conf import settings

# Set the default Django settings module for pytest
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')


def pytest_configure():
    """Configure Django settings before running tests."""
    if not settings.configured:
        settings.configure(
            DEBUG=True,
            DATABASES={
                'default': {
                    'ENGINE': 'django.db.backends.sqlite3',
                    'NAME': ':memory:',
                }
            },
            INSTALLED_APPS=[
                'django.contrib.contenttypes',
                'django.contrib.auth',
                'rest_framework',
                'rest_framework.authtoken',
                'django_filters',
                'tdm_orchestrator',
            ],
            ROOT_URLCONF='config.urls',
            REST_FRAMEWORK={
                'DEFAULT_AUTHENTICATION_CLASSES': [
                    'rest_framework.authentication.TokenAuthentication',
                ],
                'DEFAULT_PERMISSION_CLASSES': [
                    'rest_framework.permissions.IsAuthenticated',
                ],
                'UNICODE_JSON': True,
            },
            DEFAULT_AUTO_FIELD='django.db.models.BigAutoField',
        )
    django.setup()
