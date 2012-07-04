"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', #'django.db.backends.sqlite3', Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'consulting',                      # Or path to database file if using sqlite3.
        'USER': 'consulting',                      # Not used with sqlite3.
        'PASSWORD': 'consulting',                  # Not used with sqlite3.
        'HOST': '127.0.0.1',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '3306',                      # Set to empty string for default. Not used with sqlite3.
    }
}
"""

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3', #'django.db.backends.sqlite3', Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'db_consulting',                      # Or path to database file if using sqlite3.
        'USER': '',                      # Not used with sqlite3.
        'PASSWORD': '',                  # Not used with sqlite3.
        'HOST': '',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
    }
}


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
    'log',
    'cal',
    'conf',
)
