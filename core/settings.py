# -*- encoding: utf-8 -*-
"""
License: MIT
Copyright (c) 2019 - present AppSeed.us
"""

import os
from unipath import Path
import dj_database_url

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROJECT_DIR = Path(__file__).parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'S#perS3crEt_1122'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# load production server from .env
ALLOWED_HOSTS = ['localhost','192.168.178.3', '127.0.0.1', 'finance.dejong.lu']
 
# Application definition

INSTALLED_APPS = [
    # User Apps
    'apps.stocks',
    'apps.mail_relay',
    'apps.newsapi',
    'apps.predictor',
    'apps.iexcloud',
    'authentication',
    'django_celery_beat', 

    # Django defaults
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles'
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
]

# For older django version and in order to use the deprecated responsive middleware
MIDDLEWARE_CLASSES = MIDDLEWARE

# Data for responsive middleware package
RESPONSIVE_MEDIA_QUERIES = {
    'small': {
        'verbose_name': 'Small screens',
        'min_width': None,
        'max_width': 640,
    },
    'medium': {
        'verbose_name': 'Medium screens',
        'min_width': 641,
        'max_width': 1024,
    },
    'large': {
        'verbose_name': 'Large screens',
        'min_width': 1025,
        'max_width': 1440,
    },
    'xlarge': {
        'verbose_name': 'XLarge screens',
        'min_width': 1441,
        'max_width': 1920,
    },
    'xxlarge': {
        'verbose_name': 'XXLarge screens',
        'min_width': 1921,
        'max_width': None,
    }
}


ROOT_URLCONF = 'core.urls'
LOGIN_REDIRECT_URL = "home"   # Route defined in app/urls.py
LOGOUT_REDIRECT_URL = "home"  # Route defined in app/urls.py

# Main template directory
TEMPLATE_DIR = os.path.join(BASE_DIR, "core", "templates")  # ROOT dir for templates

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.request',
                # 'responsive.context_processors.device',
            ],
        },
    },
]

WSGI_APPLICATION = 'core.wsgi.application'

# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'finance_dejong_lu',
            'USER': 'chris',
            'PASSWORD': 'zuW26DMCzIUlitQhs9o8',
            'HOST': 'localhost',
            'PORT': '',
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Amsterdam'

USE_I18N = True

USE_L10N = True

USE_TZ = True

#############################################################
# SRC: https://devcenter.heroku.com/articles/django-assets

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATIC_URL = '/static/'

# Extra places for collectstatic to find static files.
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, 'core/static'),
)
#############################################################
#############################################################

# Configure django-celery
REDIS_HOST = "localhost"
BROKER_URL = "redis://127.0.0.1:6379/0"
BROKER_TRANSPORT = "redis"


