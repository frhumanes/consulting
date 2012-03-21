# -*- encoding: utf-8 -*-
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
# from userprofile.forms import ProfileForm
# from django.core.urlresolvers import reverse
# from django.http import HttpResponseRedirect
# from django.contrib.auth.models import User


# @login_required(login_url='/account/login/')
# def administrative(request):
#     return render_to_response('consulting/administrative.html', {},
#                               context_instance=RequestContext(request))


def prueba(request):
    print '*********************En prueba*********************************'
    return render_to_response('consulting/prueba.html', {},
                              context_instance=RequestContext(request))


def cargando(request):
    print '*********************En cargando*********************************'
    return render_to_response('consulting/carga.html', {},
                              context_instance=RequestContext(request))
