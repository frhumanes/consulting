
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

