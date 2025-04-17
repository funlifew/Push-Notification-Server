"""
Django settings for Push Notification Server project.

This file contains all the configuration settings for the Django project.
Settings are organized by section for better readability.
"""

from pathlib import Path
from datetime import timedelta
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# ==============================
# SECURITY SETTINGS
# ==============================

# SECURITY WARNING: keep the secret key used in production secret!
# In production, use environment variable instead of hardcoded value
SECRET_KEY = config('SECRET_KEY', default='django-insecure-&z=a1(jf#+l&b0wjzbs-l^7#&ybq*vny4r!&xf+f)e9z*9s#gu')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',')


# ==============================
# APPLICATION DEFINITION
# ==============================

INSTALLED_APPS = [
    # Django built-in apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework_simplejwt',
    "rest_framework_simplejwt.token_blacklist",
    'webpush',
    'corsheaders',
    
    # Custom apps
    'accounts',
    'server',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS middleware - must be before CommonMiddleware
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# ==============================
# DATABASE SETTINGS
# ==============================

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': config("DB_NAME"),
        'USER': config("DB_USER"),
        "PASSWORD": config("DB_PASSWORD"),
        'HOST': config("DB_HOST", default="localhost"),
        'PORT': config("DB_PORT", default=3306, cast=int),
    }
}


# ==============================
# PASSWORD VALIDATION
# ==============================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ==============================
# INTERNATIONALIZATION
# ==============================

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# ==============================
# STATIC FILES SETTINGS
# ==============================

STATIC_URL = 'static/'


# ==============================
# DEFAULT SETTINGS
# ==============================

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Use custom User model
AUTH_USER_MODEL = "accounts.User"


# ==============================
# AUTHENTICATION SETTINGS
# ==============================

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend',
    'accounts.backends.PhoneAuthBackend',
)

REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}


# ==============================
# JWT TOKEN SETTINGS
# ==============================

SIMPLE_JWT = {
    "ACCESS_TOKEN": timedelta(minutes=15),
    "REFRESH_TOKEN": timedelta(days=7),
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    'ALGORITHM': "HS256",
    'SIGNING_KEY': config("SIGNING_KEY"),
    "VERIFYING_KEY": None,
    "USER_ID_FIELD": 'id',
    'USER_ID_CLAIM': "id",
    "ACCESS_TOKEN_EXPIRE_TIME": timedelta(minutes=15),
    "REFRESH_TOKEN_EXPIRE_TIME": timedelta(days=7),
}

# JWT cookie settings
JWT_AUTH_COOKIE = "access_token"
JWT_AUTH_REFRESH_COOKIE = "refresh_token"
JWT_AUTH_SAMESITE = "Lax"
JWT_AUTH_HTTPONLY = True


# ==============================
# CORS SETTINGS
# ==============================

CORS_ALLOW_ALL_ORIGINS = True  # In production, set to False and specify CORS_ALLOWED_ORIGINS
CORS_ALLOW_CREDENTIALS = True  # Allow cookies to be sent with CORS requests

CORS_ALLOW_METHODS = [
    "GET",
    "POST",
    "PUT",
    "PATCH",
    "DELETE",
    "OPTIONS",
]

CORS_ALLOW_HEADERS = [
    "content-type",
    "authorization",
    "x-requested-with",
    "x-csrftoken",
]

APPEND_SLASH = False


# ==============================
# WEB PUSH NOTIFICATION SETTINGS
# ==============================

WEBPUSH_SETTINGS = {
    'VAPID_PUBLIC_KEY': config("VAPID_PUBLIC_KEY"),
    'VAPID_PRIVATE_KEY': config("VAPID_PRIVATE_KEY"),
    'VAPID_ADMIN_EMAIL': config("VAPID_SUBJECT")
}