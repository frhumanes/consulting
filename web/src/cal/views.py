# -*- encoding: utf-8 -*-

from datetime import date, datetime, timedelta
import time
import json

from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect, get_object_or_404

from django.contrib.auth.models import User
from django.template import RequestContext

from django.conf import settings
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect

from decorators import paginate, only_doctor

from cal.models import Slot
from cal.models import SlotType
from cal.models import Appointment

from cal.forms import SlotForm
from cal.forms import SlotTypeForm
from cal.forms import DoctorSelectionForm
from cal.forms import AppointmentForm

from cal.utils import create_calendar
from cal.utils import add_minutes
from cal.utils import get_weekday
from cal.utils import mnames
from cal.utils import get_doctor_preferences
from cal.utils import reminders


@login_required
def main(request, year=None):
    if year:
        year = int(year)
    else:
        year = time.localtime()[0]

    nowy, nowm = time.localtime()[:2]
    lst = []

    for y in [year, year + 1, year + 2]:
        mlst = []
        for n, month in enumerate(mnames):
            slot = current = False
            slots = Slot.objects.filter(date__year=y, date__month=n + 1)

            if slots:
                slot = True
            if y == nowy and n + 1 == nowm:
                current = True
            mlst.append(dict(n=n + 1, name=month, slot=slot,
                current=current))
        lst.append((y, mlst))

    data = dict(years=lst, user=request.user, year=year,
            reminders=reminders(request))

    return render_to_response("cal/app/main.html", data,
        context_instance=RequestContext(request))


@login_required
def month(request, year, month, change=None):
    year, month = int(year), int(month)

    if change in ("next", "prev"):
        now, mdelta = date(year, month, 15), timedelta(days=31)

        if change == "next":
            mod = mdelta

        elif change == "prev":
            mod = -mdelta

        year, month = (now + mod).timetuple()[:2]

    lst = create_calendar(year, month)

    if request.user.get_profile().is_doctor():
        return render_to_response("cal/doctor/month.html",
            dict(year=year, month=month, user=request.user,
                month_days=lst, mname=mnames[month - 1]),
                context_instance=RequestContext(request))
    else:
        return redirect(reverse("cal.views.doctor_calendar",
            args=(int(year), int(month))))


@login_required
@paginate(template_name='cal/doctor/list.html', list_name='events',
    objects_per_page=settings.OBJECTS_PER_PAGE)
def day(request, year, month, day):
    events = Appointment.objects.filter(date__year=year, date__month=month,
        date__day=day, doctor=request.user).order_by('start_time')

    lst = create_calendar(int(year), int(month))

    template_data = dict(year=year, month=month, day=day, user=request.user,
        month_days=lst, mname=mnames[int(month) - 1], events=events,
        context_instance=RequestContext(request))

    return template_data


@login_required
def app_add(request, year, month, day, id_doctor=None):
    if request.user.get_profile().is_doctor():
        doctor = request.user
        lst = create_calendar(int(year), int(month))
    else:
        if id_doctor:
            doctor = get_object_or_404(User, pk=int(id_doctor))
            lst = create_calendar(int(year), int(month), user=doctor)
        else:
            return HttpResponseRedirect(reverse('cal.views.main'))

    mname = mnames[int(month) - 1]

    doctor_preferences = get_doctor_preferences(year=year, month=month,
        day=day, doctor=id_doctor)

    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'doctor': doctor.id,
            'created_by': request.user.id,
            'date': date(int(year), int(month), int(day)),
            'patient': 5 #WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        })

        id_app_type = request.POST.get('app_type', None)
        start_time = request.POST.get('start_time', None)

        if id_app_type and start_time:
            app_type = get_object_or_404(SlotType, pk=int(id_app_type))
            end_time = request.POST.get('end_time', None)

            if not end_time:
                start_time = time.strptime(start_time, '%H:%M')
                end_time = add_minutes(start_time, app_type.duration)
                request_params.update({'end_time': end_time})

            request_params.update({'duration': app_type.duration,
                'app_type': app_type.id})

        form = AppointmentForm(request_params, user=doctor)
        """
        free_intervals = Appointment.objects.get_free_intervals(doctor,
        date(int(year), int(month), int(day)))

        matched = Appointment.objects.match_interval(form.save(commit=False),
                free_intervals)
        """
        if form.is_valid():
            pre_save_instance = form.save(commit=False)
            available, free_intervals = Appointment.objects.availability(
                doctor,
                date(int(year), int(month), int(day)),
                pre_save_instance)

            if available:
                form.save()

                if not request.user.get_profile().is_doctor():
                    return redirect(reverse("cal.views.doctor_day",
                        args=(int(year), int(month), int(day), doctor.id)))
                else:
                    return redirect(reverse("cal.views.day", args=(int(year),
                        int(month), int(day))))
            else:
                return render_to_response("cal/app/add.html",
                    {'form': form,
                     'year': int(year), 'month': int(month), 'day': int(day),
                     'month_days': lst,
                     'mname': mname,
                     'doctor': doctor,
                     'doctor_preferences': doctor_preferences,
                     'free_intervals': free_intervals,
                     'not_available_error': True,
                     'error_msg': _('Appointment can not be set. '\
                        'Please, choose another time interval')},
                    context_instance=RequestContext(request))
        else:
            available, free_intervals = Appointment.objects.availability(
                doctor,
                date(int(year), int(month), int(day)))
    else:
        form = AppointmentForm(user=doctor)
        available, free_intervals = Appointment.objects.availability(
            doctor,
            date(int(year), int(month), int(day)))

    return render_to_response("cal/app/add.html",
                {'form': form,
                 'year': int(year), 'month': int(month), 'day': int(day),
                 'month_days': lst,
                 'mname': mname,
                 'doctor': doctor,
                 'doctor_preferences': doctor_preferences,
                 'free_intervals': free_intervals},
                context_instance=RequestContext(request))


@login_required
def app_edit(request, pk, id_doctor=None):
    app = get_object_or_404(Appointment, pk=int(pk))

    year = int(app.date.year)
    month = int(app.date.month)
    day = int(app.date.day)

    mname = mnames[int(month) - 1]

    if not request.user.get_profile().is_doctor():
        doctor = get_object_or_404(User, pk=int(id_doctor))
        lst = create_calendar(year, month, user=doctor)
    else:
        doctor = request.user
        lst = create_calendar(year, month, user=doctor)

    doctor_preferences = get_doctor_preferences(year=year, month=month,
        day=day, doctor=id_doctor)

    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'doctor': doctor.id,
            'created_by': request.user.id,
            'date': app.date,
            'patient': 5 #WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        })

        form = AppointmentForm(request_params, instance=app, user=doctor)

        end_time = request.POST.get('end_time', None)
        if not end_time:
            start_time = request.POST.get('start_time', None)
            start_time = time.strptime(start_time, '%H:%M')
            end_time = add_minutes(start_time, app.app_type.duration)
            request_params.update({'end_time': end_time})

        selected_date = date(int(year), int(month), int(day))
        request_params.update({'duration': app.app_type.duration,
            'weekday': get_weekday(selected_date)})

        if form.is_valid():
            pre_edit_instance = form.save(commit=False)
            available, free_intervals = Appointment.objects.availability(
            doctor,
            date(int(year), int(month), int(day)),
            pre_edit_instance,
            edit=True)

            if available:
                form.save()

                if not request.user.get_profile().is_doctor():
                    return redirect(reverse("cal.views.doctor_day",
                        args=(year, month, day, doctor.id)))
                else:
                    return redirect(reverse("cal.views.day",
                        args=(year, month, day)))
            else:
                return render_to_response("cal/app/edit.html",
                {'form': form,
                 'event': app,
                 'year': year, 'month': month, 'day': day,
                 'month_days': lst,
                 'mname': mname,
                 'doctor': doctor,
                 'doctor_preferences': doctor_preferences,
                 'free_intervals': free_intervals,
                 'not_available_error': True,
                 'error_msg': _('Appointment can not be set. '\
                    'Please, choose another time interval')},
                context_instance=RequestContext(request))

        else:
            available, free_intervals = Appointment.objects.availability(
                doctor,
                date(int(year), int(month), int(day)))
    else:
        form = AppointmentForm(instance=app, user=doctor)
        available, free_intervals = Appointment.objects.availability(
            doctor,
            date(int(year), int(month), int(day)))

    return render_to_response("cal/app/edit.html",
        {'form': form,
         'event': app,
         'year': year, 'month': month, 'day': day,
         'month_days': lst,
         'mname': mname,
         'doctor': doctor,
         'doctor_preferences': doctor_preferences,
         'free_intervals': free_intervals},
        context_instance=RequestContext(request))


@login_required
def app_delete(request):
    if request.method == 'DELETE':
        data = json.loads(request.raw_post_data)
        app_id = data['app_id']

        event = get_object_or_404(Appointment, pk=int(app_id))
        event.delete()

        try:
            return HttpResponse(json.dumps({'action': 'True'}),
                status=200,
                mimetype='application/json')
        except:
            return HttpResponse(json.dumps({'action': 'False'}),
                status=200,
                mimetype='application/json')
    else:
        return HttpResponse(json.dumps({'action': 'False'}),
                status=200,
                mimetype='application/json')


@login_required
@only_doctor
@paginate(template_name='cal/slot_type/list.html',
    list_name='slot_type', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_slot_type(request):
    slot_type = SlotType.objects.filter(doctor=request.user)

    template_data = dict(user=request.user, slot_type=slot_type,
        context_instance=RequestContext(request))

    return template_data


@login_required
@only_doctor
def add_slot_type(request, template="cal/slot_type/add.html"):
    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'doctor': request.user.id,
            'created_by': request.user.id,
        })

        form = SlotTypeForm(request_params)

        if form.is_valid():
            form.save()
            return redirect(reverse("cal.list_slot_type"))
        else:
            return render_to_response(template,
                {'form': form},
                context_instance=RequestContext(request))
    else:
        form = SlotTypeForm()

    return render_to_response(template, {'form': form},
                context_instance=RequestContext(request))


@login_required
@only_doctor
def edit_slot_type(request, pk, template="cal/slot_type/edit.html"):
    slot = get_object_or_404(SlotType, pk=int(pk))

    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'doctor': request.user.id,
            'created_by': request.user.id
        })

        form = SlotTypeForm(request_params, instance=slot)

        if form.is_valid():
            form.save()
            return redirect(reverse("cal.list_slot_type"))
        else:
            return render_to_response(template,
                {"form": form, 'event': slot},
                context_instance=RequestContext(request))
    else:
        form = SlotTypeForm(instance=slot)

    return render_to_response(template,
        {"form": form, 'event': slot},
        context_instance=RequestContext(request))


@login_required
@only_doctor
def delete_slot_type(request, pk):
    slot_type = get_object_or_404(SlotType, pk=int(pk))
    slot_type.delete()
    return redirect(reverse("cal.list_slot_type"))


@login_required
@only_doctor
def list_slot(request, year, month):
    slots = Slot.objects \
        .filter(creator=request.user, date__year=year, date__month=month)

    return render_to_response('cal/slot/list.html',
        dict(slots=slots, year=int(year), month=int(month)),
        context_instance=RequestContext(request))


@login_required
@only_doctor
def add_slot(request, year, month):
    if request.method == 'POST':
        start_time = request.POST.get('start_time', None)
        id_slot_type = request.POST.get('slot_type', None)

        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
                'creator': request.user.id,
                'created_by': request.user.id,
                'date': datetime(int(year), int(month), 1)
            })

        if id_slot_type and start_time:
            slot_type = get_object_or_404(SlotType, pk=int(id_slot_type))

            start_time = time.strptime(start_time, '%H:%M')
            end_time = add_minutes(start_time, slot_type.duration)

            request_params.update({
                'end_time': end_time,
                'duration': slot_type.duration
            })

        form = SlotForm(request_params, user=request.user)

        if form.is_valid():
            form.save()
            return redirect(reverse("cal.list_slot", args=(int(year),
                int(month))))
        else:
            return render_to_response('cal/slot/add.html',
                {'form': form, 'year': year, 'month': month},
                context_instance=RequestContext(request))
    else:
        form = SlotForm(user=request.user)

    return render_to_response('cal/slot/add.html', {'form': form,
        'year': year, 'month': month},
        context_instance=RequestContext(request))


@login_required
@only_doctor
def edit_slot(request, pk):
    slot = get_object_or_404(Slot, pk=int(pk))

    if request.method == 'POST':
        start_time = request.POST.get('start_time', None)
        id_slot_type = request.POST.get('slot_type', None)

        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
                'creator': request.user.id,
                'created_by': request.user.id,
                'date': slot.date
            })

        if id_slot_type and start_time:
            event_type = get_object_or_404(SlotType, pk=int(id_slot_type))

            start_time = time.strptime(start_time, '%H:%M')
            end_time = add_minutes(start_time, event_type.duration)

            request_params.update({
                'end_time': end_time,
                'duration': event_type.duration
            })

        form = SlotForm(request_params, instance=slot, user=request.user)

        if form.is_valid():
            form.save()
            return redirect(reverse("cal.list_slot", args=(slot.date.year,
                slot.date.month)))
        else:
            return render_to_response('cal/slot/edit.html',
                {"form": form, 'slot': slot,
                 'year': slot.date.year, 'month': slot.date.month},
                context_instance=RequestContext(request))
    else:
        form = SlotForm(instance=slot, user=request.user)

    return render_to_response('cal/slot/edit.html',
        {"form": form, 'slot': slot, 'year': slot.date.year,
         'month': slot.date.month},
        context_instance=RequestContext(request))


@login_required
@only_doctor
def delete_slot(request, pk):
    slot = get_object_or_404(Slot, pk=int(pk))
    slot.delete()
    return redirect(reverse("cal.list_slot", args=(slot.date.year,
        slot.date.month)))


@login_required
def doctor_calendar(request, year, month):
    if request.method == 'POST':
        form = DoctorSelectionForm(request.POST)

        if form.is_valid():
            year, month = int(year), int(month)
            id_doctor = form.cleaned_data['doctor']
            today = time.localtime()[2:3][0]

            return redirect(reverse("cal.views.doctor_day",
                args=(int(year), int(month), int(today), int(id_doctor))))
    else:
        form = DoctorSelectionForm()

    return render_to_response('cal/app/admin.html', {'form': form,
        'year': int(year), 'month': int(month)},
        context_instance=RequestContext(request))


@login_required
def doctor_month(request, year, month, id_doctor, change=None):
    year, month = int(year), int(month)

    doctor = get_object_or_404(User, pk=int(id_doctor))
    if not doctor.get_profile().is_doctor():
        raise Http404

    # apply next / previous change
    if change in ("next", "prev"):
        now, mdelta = date(year, month, 15), timedelta(days=31)

        if change == "next":
            mod = mdelta

        elif change == "prev":
            mod = -mdelta

        year, month = (now + mod).timetuple()[:2]

    lst = create_calendar(year, month, doctor)
    doctor_preferences = get_doctor_preferences(year=year, month=month,
        doctor=id_doctor)

    return render_to_response("cal/app/month.html",
        dict(year=year, month=month, user=request.user, doctor=doctor,
            month_days=lst, mname=mnames[month - 1],
            doctor_preferences=doctor_preferences),
            context_instance=RequestContext(request))


@login_required
@paginate(template_name='cal/app/list.html',
    list_name='events', objects_per_page=settings.OBJECTS_PER_PAGE)
def doctor_day(request, year, month, day, id_doctor=None):
    doctor = get_object_or_404(User, pk=int(id_doctor))
    if not doctor.get_profile().is_doctor():
        raise Http404

    #doctor preferences

    events = Appointment.objects.filter(doctor=doctor, date__year=year,
        date__month=month, date__day=day).order_by('start_time')

    lst = create_calendar(int(year), int(month), user=doctor)
    doctor_preferences = get_doctor_preferences(year=year, month=month,
        day=day, doctor=id_doctor)

    template_data = dict(year=year, month=month, day=day, user=request.user,
        doctor=doctor, month_days=lst, mname=mnames[int(month) - 1],
        events=events, doctor_preferences=doctor_preferences,
        context_instance=RequestContext(request))

    return template_data
