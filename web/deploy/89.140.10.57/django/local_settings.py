# -*- coding: utf-8 -*-

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', #'django.db.backends.sqlite3', Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': '%(database_name)s',                      # Or path to database file if using sqlite3.
        'USER': '%(database_user)s',                      # Not used with sqlite3.
        'PASSWORD': '%(database_pass)s',                  # Not used with sqlite3.
        'HOST': '127.0.0.1',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '3306',                      # Set to empty string for default. Not used with sqlite3.
    },
    'nonrel' : {
      'ENGINE' : 'django_mongodb_engine',
      'NAME' : '%(database_name)s'
   }
}
