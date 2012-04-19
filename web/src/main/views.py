# -*- encoding: utf-8 -*-
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.conf import settings


@login_required()
def index(request):

    profile = request.user.get_profile()

    if profile.role == settings.DOCTOR:
        return render_to_response('doctor/index.html', {},
                                context_instance=RequestContext(request))
    elif profile.role == settings.ADMINISTRATIVE:
        return render_to_response('administrative/index.html', {},
                                context_instance=RequestContext(request))
    else:
        #profile.role == settings.PATIENT
        return render_to_response('patient/index.html', {},
                                context_instance=RequestContext(request))
