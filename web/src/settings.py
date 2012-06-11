# -*- encoding: utf-8 -*-

# Django settings for consulting30 project.
import os

DEBUG = True
TEMPLATE_DEBUG = DEBUG

PROJECT_ROOT = os.path.dirname(__file__)

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', #'django.db.backends.sqlite3', Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'consulting30',                      # Or path to database file if using sqlite3.
        'USER': 'consulting30',                      # Not used with sqlite3.
        'PASSWORD': 'consulting30',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}

DEFAULT_PASSWORD = '1234'

#ROLES
DOCTOR = 1
ADMINISTRATIVE = 2
PATIENT = 3

#STATUS USER
MARRIED = 1
STABLE_PARTNER = 2
DIVORCED = 3
WIDOW_ER = 4
SINGLE = 5
OTHER = 6

#SEX
WOMAN = 1
MAN = 2


#TREATMENT
BEFORE = 1
AFTER = 2

#COMPONENT
ACTIVE_INGREDIENT = 0
MEDICINE = 1

#PAGINATION
OBJECTS_PER_PAGE = 10

#STATUS APPOINTMENT
FIRST = 1
FIRST_DONE = 2
FIRST_NOT_DONE = 3
FIRST_MODIFIED = 4
FIRST_MODIFIED_DONE = 5
FIRST_MODIFIED_NOT_DONE = 6
FIRST_MODIFIED_DELETED = 7
FIRST_DELETED = 8
SUCCESSIVE = 9
SUCCESSIVE_DONE = 10
SUCCESSIVE_NOT_DONE = 11
SUCCESSIVE_MODIFIED = 12
SUCCESSIVE_MODIFIED_DONE = 13
SUCCESSIVE_MODIFIED_NOT_DONE = 14
SUCCESSIVE_MODIFIED_DELETED = 15
SUCCESSIVE_DELETED = 16

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
)

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'es-ES'

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
ADMIN_MEDIA_PREFIX = '/admin_media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = '(esgoa9774l8(aj+gp()fy&mm&s=z2y3+$bflbfj#-0vu9da%f'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.locale.LocaleMiddleware',
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
    # Uncomment the next line to enable the admin:
    'django.contrib.admin',
    # Uncomment the next line to enable admin documentation:
    # 'django.contrib.admindocs',
    'south',
    'django_extensions',
    'userprofile',
    'survey',
    'formula',
    'medicament',
    'consulting',
    'registration',
    'private_messages',
    'connector',
    'events_calendar',
)

AUTH_PROFILE_MODULE = 'userprofile.Profile'

try:
   from local_settings import *
except ImportError:
   pass
