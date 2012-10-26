
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql', #'django.db.backends.sqlite3', Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'consulting',                      # Or path to database file if using sqlite3.
        'USER': 'consulting',                      # Not used with sqlite3.
        'PASSWORD': 'consulting',                  # Not used with sqlite3.
        'HOST': '127.0.0.1',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '3306',                      # Set to empty string for default. Not used with sqlite3.
    },
    'nonrel' : {
      'ENGINE' : 'django_mongodb_engine',
      'NAME' : 'consulting'
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

"""


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
    #'south', #MONGODB ISSUE
    'django_extensions',
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
)

# Debug Toolbar
INTERNAL_IPS = ('127.0.0.1',)

"""DEBUG_TOOLBAR_PANELS = (
    'debug_toolbar.panels.version.VersionDebugPanel',
    'debug_toolbar.panels.timer.TimerDebugPanel',
    'debug_toolbar.panels.settings_vars.SettingsVarsDebugPanel',
    'debug_toolbar.panels.headers.HeaderDebugPanel',
    'debug_toolbar.panels.request_vars.RequestVarsDebugPanel',
    'debug_toolbar.panels.template.TemplateDebugPanel',
    'debug_toolbar.panels.sql.SQLDebugPanel',
    'debug_toolbar.panels.signals.SignalDebugPanel',
    'debug_toolbar.panels.logger.LoggingPanel',
)"""