# -*- encoding: utf-8 -*-

from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext

from decorators import only_doctor


@login_required
@only_doctor
def user_preferences(request):
    return render_to_response("conf/preferences.html",
        context_instance=RequestContext(request))
