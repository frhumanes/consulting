# -*- encoding: utf-8 -*-
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required


@login_required(login_url='login/register')
def index(request):
    return render_to_response('main/index.html', {},
                              context_instance=RequestContext(request))