"""
config/settings/base.py

Shared settings inherited by dev.py and prod.py.
Nothing environment-specific lives here.
"""

import environ
from pathlib import Path

# Path & Environment

BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")  # reads your .env file automatically

# Security

SECRET_KEY = env("SECRET_KEY")

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Application Definition

DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.hospitals",
    "apps.dependents",
    "apps.visits",
    "apps.reports",
    "apps.analytics",
    "apps.payments",
    "apps.notifications",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

# Middleware

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",          # must be near the top
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# URL & WSGI

ROOT_URLCONF = "config.urls"
WSGI_APPLICATION = "config.wsgi.application"

# Templates (needed for Django admin)

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Database

DATABASES = {
    'default': env.db() # It will automatically find "DATABASE_URL"

    # "default": env.db("DATABASE_URL")   #later change url for postgres

    # env.db() parses the full postgres://user:pass@host:port/dbname string
    # and returns the dict Django expects
}

# Custom User Model

AUTH_USER_MODEL = "accounts.User"
# Must be set BEFORE first migration

# Internationalization

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True  

# Static Files

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# Default Primary Key

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
# Models will override this with UUIDs where needed

# Django REST Framework

REST_FRAMEWORK = {
    # All endpoints require auth by default — opt out per view if needed
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

# drf-spectacular (API Docs)

SPECTACULAR_SETTINGS = {
    "TITLE": "FamilyPulse API",
    "DESCRIPTION": "Multi-hospital home-healthcare coordination platform",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,  # don't expose raw schema endpoint in docs UI
}

# SimpleJWT

from datetime import timedelta

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,       
    "BLACKLIST_AFTER_ROTATION": True,    
    "AUTH_HEADER_TYPES": ("Bearer",),
}