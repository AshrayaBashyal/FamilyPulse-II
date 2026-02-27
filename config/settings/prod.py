"""
config/settings/prod.py

Production settings. Inherits everything from base.py.
Stricter security. All secrets must come from environment variables.
"""

from .base import *  # noqa: F401, F403
import environ

env = environ.Env()

# Security

DEBUG = False

ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")  # comma-separated in .env

# HTTPS enforcement
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000         # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS — only allow explicitly listed origins

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS")

# ---------------------------------------------------------------------------
# Email — configure a real backend in prod (e.g. SendGrid, SES)
# We'll set this up in the notifications phase
# ---------------------------------------------------------------------------

EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"