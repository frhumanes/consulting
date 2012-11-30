from django.conf import settings
from datetime import datetime

def session(request):
    expired = False
    if request.user.is_authenticated():
        try:
            delta = datetime.today()-request.user.get_profile().updated_password_at
            expired = delta.days>settings.PASSWORD_EXPIRATION_DAYS
        except: 
            pass
    if not 'timeout' in request.session:
        request.session['timeout'] = settings.SESSION_COOKIE_AGE
    return {'SESSION_TIMEOUT': settings.SESSION_COOKIE_AGE,
            'TODAY':datetime.today(),
            'EXPIRED_PASSWORD': expired}