from django.contrib.auth import authenticate, login
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from registration.forms import UserRegistrationForm
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils.translation import ugettext_lazy as _


def login_consulting(request, redirect_field_name=REDIRECT_FIELD_NAME,
                        form_class=UserRegistrationForm):

    if request.method == 'POST':
        form = form_class(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            user = authenticate(username=username, password=password)

            if user is not None:
                if user.is_active:
                    login(request, user)
                    # Redirect to a success page.
                    return HttpResponseRedirect(reverse('main_index'))
                else:
                    # Return a 'disabled account' error message
                    return HttpResponseRedirect(reverse('main_index'))
            else:
                # Return an 'invalid login' error message.
                return HttpResponseRedirect(reverse('main_index'))
    else:
        form = form_class()

    return render_to_response('registration/login.html',
        {'form': form},
        context_instance=RequestContext(request))


def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect(reverse('login'))
