from django.contrib.auth import login
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from registration.forms import UserRegistrationForm
from django.contrib.auth import REDIRECT_FIELD_NAME


def login_consulting30(request, redirect_field_name=REDIRECT_FIELD_NAME,
                        form_class=UserRegistrationForm):
    # next = redirect_field_name
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    if request.method == "POST":
        form = form_class(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)

            if redirect_to:
                return HttpResponseRedirect(redirect_to)
            else:
                return HttpResponseRedirect(reverse('main_index'))
    else:
        form = form_class(request)

    return render_to_response('registration/login.html',
                                {'form': form, 'redirect_to': redirect_to},
                                context_instance=RequestContext(request))


def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect(reverse('login'))
