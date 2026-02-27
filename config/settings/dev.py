"""
config/settings/dev.py

Development settings. Inherits everything from base.py.
This file is only used locally — never in production.
"""

from .base import *  # noqa: F401, F403

# Dev-only overrides

DEBUG = True

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# CORS — allow all origins locally 

CORS_ALLOW_ALL_ORIGINS = True

# Email — print to console instead of sending real emails

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"