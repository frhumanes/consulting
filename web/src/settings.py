# -*- encoding: utf-8 -*-

# Django settings for cronos30 project.
import os

DEBUG = True
TEMPLATE_DEBUG = False

PROJECT_ROOT = os.path.dirname(__file__)

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'cronos',
        'USER': 'cronos',
        'PASSWORD': 'cronos',
        'HOST': '127.0.0.1',
        'PORT': '3306',
    },
    'nonrel': {
        'ENGINE': 'django_mongodb_engine',
        'NAME': 'cronos'
    }
}

# The absolute path to the directory where collectstatic will collect static
# files for deployment.
STATIC_ROOT = os.path.join(PROJECT_ROOT, 'statics')

# URL to use when referring to static files located in STATIC_ROOT
STATIC_URL = '/static/'

# This setting defines the additional locations the staticfiles app will traverse
# if the FileSystemFinder finder is enabled, e.g. if you use the collectstatic
# or findstatic management command or use the static file serving view
STATICFILES_DIRS = (os.path.join(PROJECT_ROOT, 'static'),
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
)

STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
)

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'Europe/Madrid'

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.contrib.messages.context_processors.messages",
    "django.core.context_processors.request",
    "context_processors.session"
)

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'es'

gettext = lambda s: s
LANGUAGES = (
    ('es', gettext('Spanish')),
    ('en', gettext('English')),
)

LOGIN_URL = '/accounts/login/'

LOGIN_REDIRECT_URL = '/'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = os.path.join(PROJECT_ROOT, 'media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
ADMIN_MEDIA_PREFIX = os.path.join(STATIC_URL, 'admin', '')

# Make this unique, and don't share it with anybody.
SECRET_KEY = '(esgoa9774l8(aj+gp()fy&mm&s=z2y3+$bflbfj#-0vu9da%f'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#    'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    #'debug_toolbar.middleware.DebugToolbarMiddleware',
    #'django.middleware.cache.UpdateCacheMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    #'django.middleware.cache.FetchFromCacheMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    os.path.join(PROJECT_ROOT, "templates"),
)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    #'south', #MONGODB ISSUE
    'django_extensions',
    'django_memcached',
    'memcache_status',
    'userprofile',
    'survey',
    'formula',
    'medicament',
    'consulting',
    'registration',
    'private_messages',
    'log',
    'cal',
    'conf',
    'illness',
    'stadistic',
    #'debug_toolbar',
    'cronos'
)

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'LOCATION': '127.0.0.1:11211',
        'TIMEOUT': 7 * 24 * 60 * 60,
        'KEY_PREFIX': 'cronos'
    }
}
DJANGO_MEMCACHED_REQUIRE_STAFF = True

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

AUTH_PROFILE_MODULE = 'userprofile.Profile'
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_AGE = 30*60 # in seconds
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
try:
    DATABASE_ROUTERS = ['stadistic.StadisticRouter']
    from app_config import *
    from local_settings import *
except ImportError:
    pass

if 'cronos' in INSTALLED_APPS:
    FORCE_SCRIPT_NAME = ""
    _prefix = (FORCE_SCRIPT_NAME or "")
    LOGIN_URL = '/portal/login'
    LOGIN_URL = _prefix + LOGIN_URL
    LOGIN_URL_REDIRECT = _prefix + LOGIN_URL
    LOGOUT_REDIRECT = '/portal/logout'
    LOGOUT_URL = _prefix + LOGOUT_REDIRECT
    MEDIA_URL = _prefix + MEDIA_URL
    STATIC_URL = _prefix + STATIC_URL
    #AT4_SERVER = "http://localhost:8000"
    AT4_SERVER = "https://195.57.0.149:20000"
    #AUTH_RESOURCE = "/portal/utilUserController.at4"
    AUTH_RESOURCE = "/Cronos/utilUserController.at4"
    VIDEOCONFERENCE_SERVER = 'https://89.140.10.39'
