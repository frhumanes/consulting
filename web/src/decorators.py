# -*- encoding: utf-8 -*-

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.http import HttpResponseRedirect
from django.core.urlresolvers import reverse
from functools import wraps
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.core.exceptions import PermissionDenied
from datetime import datetime


def paginate(template_name=None, list_name='default', objects_per_page=10):
    def inner_p(fn):
        def wrapped(request, *args, **kwargs):
            fn_res = fn(request, *args, **kwargs)
            objects = fn_res[list_name]

            paginator = Paginator(objects, objects_per_page)
            try:
                page = int(request.GET.get('page', '1'))
            except ValueError:
                page = 1

            # If page request (9999) is out of range,
            # deliver last page of results.
            try:
                loo = paginator.page(page)
            except (EmptyPage, InvalidPage):
                loo = paginator.page(paginator.num_pages)

            fn_res.update({list_name: loo})
            if 'template_name' in fn_res:
                return render_to_response(fn_res['template_name'], fn_res,
                context_instance=RequestContext(request))
            else:
                return render_to_response(template_name, fn_res,
                context_instance=RequestContext(request))
        return wraps(fn)(wrapped)
    return inner_p


def only_doctor(func):
    def _fn(request, *args, **kwargs):
        if request.user.get_profile().is_doctor():
            return func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('cal.views.main'))

    return _fn


def only_doctor_consulting(func):
    def _fn(request, *args, **kwargs):
        if request.user.get_profile().is_doctor():
            if 'patient_user_id' in kwargs and not request.user.doctor.filter(user__id=kwargs['patient_user_id']):
                raise PermissionDenied
            if 'id_patient' in kwargs and not request.user.doctor.filter(user__id=kwargs['id_patient']):
                raise PermissionDenied
            if 'id_task' in kwargs and not request.user.doctor.filter(user__patient_tasks__id=kwargs['id_task']):
                raise PermissionDenied
            if 'id_appointment' in kwargs and not request.user.doctor.filter(user__appointment_patient__id=kwargs['id_appointment']):
                raise PermissionDenied
            return func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('consulting_index'))

    return _fn


def only_patient_consulting(func):
    def _fn(request, *args, **kwargs):
        if request.user.get_profile().is_patient():
            return func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('consulting_index'))

    return _fn


def only_doctor_administrative(func):
    def _fn(request, *args, **kwargs):
        if request.user.get_profile().is_administrative() or\
            request.user.get_profile().is_doctor():
            return func(request, *args, **kwargs)
        else:
            return HttpResponseRedirect(reverse('consulting_index'))

    return _fn

def update_password_date(func):
    def _fn(request, *args, **kwargs):
        prof = request.user.get_profile()
        prof.updated_password_at = datetime.today()
        prof.save()
        return func(request, *args, **kwargs)
        
    return _fn