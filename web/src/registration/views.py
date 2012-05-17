# -*- encoding: utf-8 -*-
# from django.contrib.auth import authenticate, login
# from django.shortcuts import render_to_response, redirect
# from django.template import RequestContext
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
# from registration.forms import UserRegistrationForm


# def login_consulting(request, form_class=UserRegistrationForm):

#     if request.method == 'POST':
#         next = request.POST.get('next', 'index')
#         form = form_class(data=request.POST)
#         # form.non_field_errors(in template login.html) controls
#         # if account isn't active or username or password aren't correct
#         # If username and password are correct you can carry on

#         if form.is_valid():
#             username = form.cleaned_data['username']
#             password = form.cleaned_data['password']
#             user = authenticate(username=username, password=password)
#             login(request, user)

#             # return HttpResponseRedirect(reverse('index'))
#             return redirect(next)
#     else:
#         next = request.GET.get('next', 'index')
#         form = form_class()

#     return render_to_response('registration/login.html',
#                                 {'form': form, 'next': next},
#                                 context_instance=RequestContext(request))


def logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseRedirect(reverse('login'))
