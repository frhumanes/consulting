def session(request):
    from django.conf import settings
    if not 'timeout' in request.session:
    	request.session['timeout'] = settings.SESSION_COOKIE_AGE
    return {'SESSION_TIMEOUT': settings.SESSION_COOKIE_AGE}