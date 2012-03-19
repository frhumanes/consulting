from django.contrib.auth import login
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from registration.forms import UserRegistrationForm


def register(request, form_class=UserRegistrationForm):
    if request.method == "POST":
        form = form_class(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return HttpResponseRedirect(reverse('main_index'))
    else:
        form = form_class(request)

    return render_to_response('registration/registration.html',
                                {'form': form},
                                context_instance=RequestContext(request))


def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect(reverse('register'))
