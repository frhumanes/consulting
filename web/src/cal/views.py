# -*- encoding: utf-8 -*-

from datetime import date, datetime, timedelta
from datetime import time as ttime
import time
import json

from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils import simplejson
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.forms.util import ErrorList


from django.contrib.auth.models import User
from django.template import RequestContext

from django.conf import settings
from django.http import Http404
from django.http import HttpResponse
from django.http import HttpResponseRedirect

from decorators import paginate
from decorators import only_doctor
from decorators import only_doctor_administrative

from userprofile.models import Profile
from cal.models import Slot
from cal.models import SlotType
from cal.models import Appointment
from cal.models import Vacation
from cal.models import Event

from cal.forms import SlotForm
from cal.forms import SlotTypeForm
from cal.forms import DoctorSelectionForm
from cal.forms import AppointmentForm
from cal.forms import VacationForm
from cal.forms import EventForm

from cal.utils import create_calendar
from cal.utils import add_minutes
from cal.utils import get_weekday
from cal.utils import mnames
from cal.utils import get_doctor_preferences
from cal.utils import check_vacations


@login_required
@only_doctor_administrative
def index(request):
    if 'appointment' in request.session:
        del request.session['appointment']
    if 'illness' in request.session:
        del request.session['illness']

    return render_to_response("cal/main/index_cal.html", dict(year = time.localtime()[0],month = time.localtime()[1]),
        context_instance=RequestContext(request))


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

    today = time.localtime()[2:3][0]

    data = dict(years=lst, user=request.user, year=year, today=today)

    return render_to_response("cal/app/main.html", data,
        context_instance=RequestContext(request))


@login_required
def select_month_year(request, year=None):
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
            slots = Slot.objects.filter(year=y, month=n)

            if slots:
                slot = True
            if y == nowy and n + 1 == nowm:
                current = True
            mlst.append(dict(n=n + 1, name=month, slot=slot,
                current=current))
        lst.append((y, mlst))

    today = time.localtime()[2:3][0]

    data = dict(years=lst, user=request.user, year=year, today=today)

    return render_to_response("cal/app/select_month_year.html",
        data, context_instance=RequestContext(request))


@login_required
def scheduler(request, id_patient, year=None):
    patient = get_object_or_404(User, pk=int(id_patient))
    if patient.get_profile().is_patient() and patient.get_profile().doctor is None:
        return HttpResponseRedirect(reverse('cal.select_doctor', args=[id_patient]))
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
            slots = Slot.objects.filter(year=y, month=n)

            if slots:
                slot = True
            if y == nowy and n + 1== nowm:
                current = True
            mlst.append(dict(n=n + 1, name=month, slot=slot,
                current=current))
        lst.append((y, mlst))

    today = time.localtime()[2:3][0]

    data = dict(years=lst, year=year, month=nowm, today=today,
            patient_user=patient, doctor=patient.get_profile().doctor)

    return render_to_response("cal/app/scheduler.html",
        data, context_instance=RequestContext(request))


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

    if request.user.get_profile().is_doctor():
        lst = create_calendar(year, month, doctor=request.user)
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
def day(request, year, month, day, id_user, change=None):
    user = User.objects.get(pk=int(id_user))
    if user.get_profile().is_doctor():
        doctor = user
        patient = None
    else:
        doctor = user.get_profile().doctor
        patient = user

    if change in ("next", "prev"):
        now, mdelta = date(int(year), int(month), int(day)), timedelta(days=1)

        if change == "next":
            mod = mdelta

        elif change == "prev":
            mod = -mdelta

        year, month, day= (now + mod).timetuple()[:3]

    events = Appointment.objects.filter(date__year=year, date__month=month,
            date__day=day, doctor=doctor).order_by('start_time')
    vacations = check_vacations(doctor, year, month, day)
    lst = create_calendar(int(year), int(month), doctor=doctor)
    doctor_preferences = get_doctor_preferences(year=year, month=month,
                day=day, doctor=doctor.id)

    available, free_intervals = Appointment.objects.availability(
                doctor,
                date(int(year), int(month), int(day)))

    template_data = dict(year=year, month=month, day=day, vacations=vacations,
        doctor=doctor, month_days=lst, mname=mnames[int(month) - 1],
        events=events, free_intervals=free_intervals,
        patient_user=patient, doctor_preferences=doctor_preferences,
        context_instance=RequestContext(request))

    return template_data

@login_required
def calendar(request, year, month, day, id_user, change='this'):

    if change in ("next", "prev"):
        now, mdelta = date(int(year), int(month), 15), timedelta(days=31)

        if change == "next":
            mod = mdelta

        elif change == "prev":
            mod = -mdelta

        year, month = (now + mod).timetuple()[:2]


    user = User.objects.get(pk=int(id_user))
    if user.get_profile().is_doctor():
        doctor = user
        patient = None
    else:
        doctor = user.get_profile().doctor
        patient = user
    lst = create_calendar(int(year), int(month), doctor=doctor)
    if int(day):
        available, free_intervals = Appointment.objects.availability(doctor,
                date(int(year), int(month), int(day)))
        doctor_preferences = get_doctor_preferences(year=year, month=month,
                day=day, doctor=doctor.id)
    else:
        available, free_intervals, doctor_preferences = [],[],[]

    return render_to_response('cal/includes/calendar.html', 
                                dict(year=year, month=month, day=day,
                                 doctor=doctor, month_days=lst, 
                                 patient_user=patient, 
                                 mname=mnames[int(month) - 1],
                                 free_intervals=free_intervals,
                                 doctor_preferences=doctor_preferences),
        context_instance=RequestContext(request))


@login_required
def calendar_big(request, year, month, change='this', id_doctor=None):

    if change in ("next", "prev"):
        now, mdelta = date(int(year), int(month), 15), timedelta(days=31)

        if change == "next":
            mod = mdelta

        elif change == "prev":
            mod = -mdelta

        year, month = (now + mod).timetuple()[:2]

    if id_doctor:
        doctor = User.objects.get(pk=int(id_doctor))
        lst = create_calendar(int(year), int(month), doctor=doctor)
    else:
        doctor = None
        lst = create_calendar(int(year), int(month), doctor=request.user)

    doctors = Profile.objects.filter(role=settings.DOCTOR).order_by('first_surname', 'second_surname','name')

    form = DoctorSelectionForm()

    return render_to_response('cal/includes/calendar_big.html', 
                                dict(year=year, month=month, doctors=doctors,
                                 doctor=doctor, month_days=lst, 
                                 mname=mnames[int(month) - 1], form = form),
        context_instance=RequestContext(request))


@login_required
@paginate(template_name='cal/doctor/list_consultation.html',
    list_name='events', objects_per_page=settings.OBJECTS_PER_PAGE)
def day_consultation(request, year, month, day):
    events = Appointment.objects.filter(date__year=year, date__month=month,
            date__day=day, doctor=request.user).order_by('start_time')

    lst = create_calendar(int(year), int(month), doctor=request.user)

    available, free_intervals = Appointment.objects.availability(
                request.user,
                date(int(year), int(month), int(day)))

    template_data = dict(year=year, month=month, day=day,
        user=request.user, month_days=lst, mname=mnames[int(month) - 1],
        events=events, free_intervals=free_intervals,
        context_instance=RequestContext(request))

    return template_data


@login_required
def app_add(request, year, month, day, id_user):
    user = User.objects.get(pk=int(id_user))
    if user.get_profile().is_doctor():
        doctor = user
        patient = None
    else:
        doctor = user.get_profile().doctor
        patient = user

    lst = create_calendar(int(year), int(month), doctor=doctor)
    vacations = check_vacations(doctor, year, month, day)

    if vacations:
        return render_to_response("cal/app/edit.html",
                {'vacations': vacations,
                 'year': int(year), 'month': int(month), 'day': int(day),
                 'month_days': lst,
                 'doctor': doctor,
                 'patient_user': patient,
                 'not_available_error': True,
                 'error_msg': _('Appointment can not be set. '\
                    'Please, choose another time interval')},
                context_instance=RequestContext(request))

    mname = mnames[int(month) - 1]

    doctor_preferences = get_doctor_preferences(year=year, month=month,
        day=day, doctor=doctor.id)

    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'doctor': doctor.id,
            'created_by': request.user.id,
            'date': date(int(year), int(month), int(day)),
            'patient': patient.id # WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        })

        id_app_type = request.POST.get('app_type', None)
        start_time = request.POST.get('start_time', None)
        end_time = request.POST.get('end_time', None)

        if id_app_type:
            app_type = get_object_or_404(SlotType, pk=int(id_app_type))
            duration = app_type.duration
            request_params.update({'app_type': app_type.id})

            if end_time:
                end_time = time.strptime(end_time, '%H:%M')
                end_time = ttime(end_time[3], end_time[4], end_time[5])

                if start_time:
                    start_time = time.strptime(start_time, '%H:%M')
                    start_time = ttime(start_time[3], start_time[4], start_time[5])
                    duration = ((datetime.combine(date.today(), end_time) - \
                        datetime.combine(date.today(), start_time)).seconds) / 60
                    #del request_params['app_type']
            else:
                if start_time:
                    start_time = time.strptime(start_time, '%H:%M')
                    end_time = add_minutes(start_time, duration)
                    start_time = ttime(start_time[3], start_time[4], start_time[5])

            request_params.update({'start_time': start_time,
                    'end_time': end_time, 'duration': duration})
        else:
            if start_time and end_time:
                start_time = time.strptime(start_time, '%H:%M')
                start_time = ttime(start_time[3], start_time[4], start_time[5])

                end_time = time.strptime(end_time, '%H:%M')
                end_time = ttime(end_time[3], end_time[4], end_time[5])

                duration = (datetime.combine(date.today(), end_time) - \
                    datetime.combine(date.today(), start_time)).seconds

                request_params.update({'start_time': start_time,
                    'end_time': end_time, 'duration': duration / 60})

        form = AppointmentForm(request_params, user=doctor)

        if form.is_valid():
            pre_save_instance = form.save(commit=False)
            available, free_intervals = Appointment.objects.availability(
                doctor,
                date(int(year), int(month), int(day)),
                pre_save_instance)

            if available:
                form.save()

                if 'appointment' in request.session:
                    return redirect(reverse("consulting_main",
                        kwargs={'id_appointment':request.session['appointment'].id,
                            'code_illness':request.session['illness'].code}))
                else:
                    return redirect(reverse("cal.views.day",
                        args=(int(year), int(month), int(day), doctor.id)))
            else:
                return render_to_response("cal/app/add.html",
                    {'form': form,
                     'year': int(year), 'month': int(month), 'day': int(day),
                     'month_days': lst,
                     'mname': mname,
                     'doctor': doctor,
                     'patient_user': patient,
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
                 'patient_user': patient,
                 'doctor_preferences': doctor_preferences,
                 'free_intervals': free_intervals},
                context_instance=RequestContext(request))


@login_required
def app_edit(request, pk, id_patient=None, id_doctor=None):
    app = get_object_or_404(Appointment, pk=int(pk))
    if app.date < date.today():
        raise Http404

    patient = app.patient
    doctor = app.doctor

    year = int(app.date.year)
    month = int(app.date.month)
    day = int(app.date.day)

    mname = mnames[int(month) - 1]

    lst = create_calendar(year, month, doctor=doctor)

    vacations = check_vacations(doctor, year, month, day)

    if vacations:
        return render_to_response("cal/app/edit.html",
                {'vacations': vacations},
                context_instance=RequestContext(request))

    doctor_preferences = get_doctor_preferences(year=year, month=month,
        day=day, doctor=doctor.id)


    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'doctor': doctor.id,
            'created_by': request.user.id,
            'date': app.date,
            'patient': patient.id # WARNING!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        })

        start_time = request.POST.get('start_time', None)
        end_time = request.POST.get('end_time', None)
        app_type = request.POST.get('app_type', None)

        if not app_type is None and not app_type == '':
            app_type = get_object_or_404(SlotType, pk=int(app_type))

            duration = app_type.duration
            request_params.update({'app_type': app_type.id})

            if end_time:
                end_time = time.strptime(end_time, '%H:%M')
                end_time = ttime(end_time[3], end_time[4], end_time[5])

                if start_time:
                    start_time = time.strptime(start_time, '%H:%M')
                    start_time = ttime(start_time[3], start_time[4], start_time[5])
                    duration = (datetime.combine(date.today(), end_time) - \
                        datetime.combine(date.today(), start_time)).seconds / 60
                    #del request_params['app_type']
            else:
                if start_time:
                    start_time = time.strptime(start_time, '%H:%M')
                    end_time = add_minutes(start_time, duration)
                    start_time = ttime(start_time[3], start_time[4], start_time[5])

            request_params.update({'start_time': start_time,
                    'end_time': end_time, 'duration': duration})
        else:
            if end_time:
                end_time = time.strptime(end_time, '%H:%M')
                end_time = ttime(end_time[3], end_time[4], end_time[5])

                if start_time:
                    start_time = time.strptime(start_time, '%H:%M')
                    start_time = ttime(start_time[3], start_time[4], start_time[5])

                    duration = datetime.combine(date.today(), end_time) - \
                        datetime.combine(date.today(), start_time)
                    request_params.update({'end_time': end_time,
                        'start_time': start_time,
                        'duration': duration.seconds / 60})

        selected_date = date(int(year), int(month), int(day))
        request_params.update({'weekday': get_weekday(selected_date)})

        form = AppointmentForm(request_params, instance=app, user=doctor)

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
                    return redirect(reverse("doctor_day",
                        args=(doctor.id, year, month, day)))
                else:
                    return redirect(reverse("cal.views.day",
                        args=(year, month, day, doctor.id)))
            else:
                return render_to_response("cal/app/edit.html",
                {'form': form,
                 'event': app,
                 'year': year, 'month': month, 'day': day,
                 'month_days': lst,
                 'mname': mname,
                 'doctor': doctor,
                 'patient_user': patient,
                 'doctor_preferences': doctor_preferences,
                 'free_intervals': free_intervals,
                 'not_available_error': True,
                 'error_msg': _('No se pudo crear la cita. '\
                    'Por favor, seleccione un intervalo de tiempo disponible')},
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
         'patient_user': patient,
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
            return HttpResponse(json.dumps({'action': True}),
                status=200,
                mimetype='application/json')
        except:
            return HttpResponse(json.dumps({'action': False}),
                status=200,
                mimetype='application/json')
    else:
        return HttpResponse(json.dumps({'action': False}),
                status=200,
                mimetype='application/json')


@login_required
@paginate(template_name='cal/patient/list.html',
    list_name='events', objects_per_page=settings.OBJECTS_PER_PAGE)
def app_list_patient(request, id_patient):
    patient = get_object_or_404(User, pk=int(id_patient))
    events = Appointment.objects.filter(patient=patient).order_by('-date')

    template_data = dict(events=events, doctor=patient.get_profile().doctor,
                        patient=patient,
                        context_instance=RequestContext(request))

    return template_data


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
                {"form": form, 'slot_type': slot},
                context_instance=RequestContext(request))
    else:
        form = SlotTypeForm(instance=slot)

    return render_to_response(template,
        {"form": form, 'slot_type': slot},
        context_instance=RequestContext(request))


@login_required
@only_doctor
def delete_slot_type(request):
    if request.method == 'DELETE':
        data = json.loads(request.raw_post_data)
        pk = data['pk']

        slot_type = get_object_or_404(SlotType, pk=int(pk))

        try:
            slot_type.delete()
            return HttpResponse(json.dumps({'action': True}),
                status=200,
                mimetype='application/json')
        except:
            return HttpResponse(json.dumps({'action': False}),
                status=200,
                mimetype='application/json')
    else:
        return HttpResponse(json.dumps({'action': False}),
                status=200,
                mimetype='application/json')


@login_required
@only_doctor
def list_slot(request, year=None):
    if not year:
        year = time.localtime()[0]
    slots = Slot.objects.filter(creator=request.user, year=int(year))

    return render_to_response('cal/slot/list.html',
        dict(slots=slots, year=int(year)),
        context_instance=RequestContext(request))


@login_required
@only_doctor
def add_slot(request, year, month=1):
    if request.method == 'POST':
        start_time = request.POST.get('start_time', None)
        end_time = request.POST.get('end_time', None)
        id_slot_type = request.POST.get('slot_type', None)
        months = request.POST.getlist('months')
        weekdays = request.POST.getlist('weekdays')

        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'months': months,
            'weekdays': weekdays,
            })
        slot_type = get_object_or_404(SlotType, pk=int(id_slot_type))

        if id_slot_type and start_time and not end_time:
            st = time.strptime(start_time, '%H:%M')
            end_time = add_minutes(st, slot_type.duration)

            

        form = SlotForm(request_params, user=request.user)

        if form.is_valid():
            for m in months:
                for d in weekdays:
                    s = Slot()
                    s.weekday = d
                    s.month = m
                    s.year = int(year)
                    s.start_time = start_time
                    s.end_time = end_time
                    s.creator = request.user
                    s.created_by = request.user
                    s.description = form.cleaned_data['description']
                    s.slot_type = slot_type
                    s.save()
            return redirect(reverse("cal.list_slot", args=(int(year),
                )))
        else:
            return render_to_response('cal/slot/add.html',
                {'form': form, 'year': year,},
                context_instance=RequestContext(request))
    else:
        form = SlotForm(user=request.user)

    return render_to_response('cal/slot/add.html', {'form': form,
        'year': year,},
        context_instance=RequestContext(request))


@login_required
@only_doctor
def edit_slot(request, pk):
    slot = get_object_or_404(Slot, pk=int(pk))

    if request.method == 'POST':
        start_time = request.POST.get('start_time', None)
        end_time = request.POST.get('end_time', None)
        id_slot_type = request.POST.get('slot_type', None)
        months = request.POST.get('months')
        weekdays = request.POST.get('weekdays')

        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'months': months,
            'weekdays': weekdays,
            })
        slot_type = get_object_or_404(SlotType, pk=int(id_slot_type))

        if id_slot_type and start_time and not end_time:
            st = time.strptime(start_time, '%H:%M')
            end_time = add_minutes(st, slot_type.duration)

        form = SlotForm(request_params, user=request.user, slot=slot)

        if form.is_valid():
            s = slot
            s.weekday = weekdays
            s.month = months
            s.start_time = start_time
            s.end_time = end_time
            s.creator = request.user
            s.created_by = request.user
            s.description = form.cleaned_data['description']
            s.slot_type = slot_type
            s.save()
            return redirect(reverse("cal.list_slot", args=(slot.year,
                )))
        else:
            return render_to_response('cal/slot/edit.html',
                {"form": form, 'slot': slot,
                 'year': slot.year, 'month': slot.month},
                context_instance=RequestContext(request))
    else:
        form = SlotForm( dict(weekdays=[slot.weekday], months=[slot.month], start_time=slot.start_time, end_time=slot.end_time, slot_type=slot.slot_type), user=request.user, slot=slot)

    return render_to_response('cal/slot/edit.html',
        {"form": form, 'slot': slot, 'year': slot.year,
         'month': slot.month},
        context_instance=RequestContext(request))


@login_required
@only_doctor
def delete_slot(request, pk):
    slot = get_object_or_404(Slot, pk=int(pk))
    year = int(slot.year)
    slot.delete()
    return redirect(reverse("cal.list_slot", args=(year,)))


@login_required
def doctor_calendar(request):
    if request.method == 'POST':
        form = DoctorSelectionForm(request.POST)
        if form.is_valid():
            
            id_doctor = form.cleaned_data['doctor']

            return redirect(reverse("cal.scheduler",
                args=[int(id_doctor),]))
    else:
        form = DoctorSelectionForm()

    return render_to_response('cal/app/admin.html', {'form': form},
        context_instance=RequestContext(request))


@login_required
def doctor_month(request, year, month, id_doctor, change=None):
    year, month = int(year), int(month)

    doctor = get_object_or_404(User, pk=int(id_doctor))
    if not doctor.get_profile().is_doctor():
        raise Http404

    if change in ("next", "prev"):
        now, mdelta = date(year, month, 15), timedelta(days=31)

        if change == "next":
            mod = mdelta

        elif change == "prev":
            mod = -mdelta

        year, month = (now + mod).timetuple()[:2]

    lst = create_calendar(year, month, doctor=doctor)
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
def doctor_day(request, id_doctor, year, month, day):
    doctor = get_object_or_404(User, pk=int(id_doctor))
    if not doctor.get_profile().is_doctor():
        raise Http404

    vacations = check_vacations(doctor, year, month, day)

    if not vacations:
        events = Appointment.objects.filter(doctor=doctor, date__year=year,
            date__month=month, date__day=day).order_by('start_time')
    else:
        events = Appointment.objects.none()

    lst = create_calendar(int(year), int(month), doctor=doctor)
    doctor_preferences = get_doctor_preferences(year=year, month=month,
        day=day, doctor=id_doctor)

    available, free_intervals = Appointment.objects.availability(
                doctor,
                date(int(year), int(month), int(day)))

    template_data = dict(year=year, month=month, day=day, user=request.user,
        doctor=doctor, month_days=lst, mname=mnames[int(month) - 1],
        events=events, doctor_preferences=doctor_preferences,
        vacations=vacations, free_intervals=free_intervals,
        context_instance=RequestContext(request))

    return template_data


@login_required
@only_doctor
@paginate(template_name='cal/vacation/list.html',
    list_name='vacations', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_vacation(request):
    vacations = Vacation.objects.filter(doctor=request.user).order_by('-date')
    template_data = dict(user=request.user, vacations=vacations,
        context_instance=RequestContext(request))

    return template_data


@login_required
@only_doctor
def add_vacation(request, template="cal/vacation/add.html"):
    if request.method == 'POST':
        start_date = request.POST.get('date', None)
        end_date = request.POST.get('end_date', start_date)
        if not end_date:
            end_date = start_date
        error = None
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'doctor': request.user.id,
            'created_by': request.user.id,
            'date': start_date
        })
        form = VacationForm(request_params)
        form.is_valid()
        start_date = datetime.strptime(start_date, settings.DATE_FORMAT)
        end_date = datetime.strptime(end_date, settings.DATE_FORMAT)
        if end_date and end_date >= start_date:
            for n in set([0]+range(int((end_date - start_date).days))):
                if Appointment.objects.filter(doctor=request.user, date=(start_date + timedelta(n))).count():
                    form._errors['__all__'] = ErrorList([u"Existen citas concertadas en el intervalo de vacaciones. Elija otro intervalo de fechas o modifique las citas concertadas."])
                    error = True
                    break
        else:
            form._errors['end_date'] = ErrorList([u"Fecha final debe ser mayor que la fecha inicial"])
            error = True

        if not error:
            for n in set([0]+range(int ((end_date - start_date).days))):
                request_params.update({
                    'date': (start_date + timedelta(n)).strftime(settings.DATE_FORMAT)
                })    

                form = VacationForm(request_params)

                if form.is_valid():
                    form.save()
                else:
                     return render_to_response(template,
                        {'form': form},
                        context_instance=RequestContext(request))
            return redirect(reverse("cal.list_vacation"))
        else:
            return render_to_response(template,
                {'form': form},
                context_instance=RequestContext(request))
    else:
        form = VacationForm()

    return render_to_response(template, {'form': form},
                context_instance=RequestContext(request))


@login_required
@only_doctor
def edit_vacation(request, pk, template="cal/vacation/edit.html"):
    vacation = get_object_or_404(Vacation, pk=int(pk))

    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'doctor': request.user.id,
            'created_by': request.user.id,
        })

        date = request.POST.get('date', None)
        if date:
            date = datetime.now().strptime(date, settings.DATE_FORMAT)
            request_params.update({'date': date})

        form = VacationForm(request_params, instance=vacation)

        if form.is_valid():
            form.save()
            return redirect(reverse("cal.list_vacation"))
        else:
            return render_to_response(template,
                {"form": form, 'vacation': vacation},
                context_instance=RequestContext(request))
    else:
        form = VacationForm(instance=vacation)

    return render_to_response(template,
        {"form": form, 'vacation': vacation},
        context_instance=RequestContext(request))


@login_required
@only_doctor
def delete_vacation(request):
    if request.method == 'DELETE':
        data = json.loads(request.raw_post_data)
        pk = data['pk']

        vacation = get_object_or_404(Vacation, pk=int(pk))

        try:
            vacation.delete()
            return HttpResponse(json.dumps({'action': True}),
                status=200,
                mimetype='application/json')
        except:
            return HttpResponse(json.dumps({'action': False}),
                status=200,
                mimetype='application/json')
    else:
        return HttpResponse(json.dumps({'action': False}),
                status=200,
                mimetype='application/json')


@login_required
@only_doctor
@paginate(template_name='cal/event/list.html',
    list_name='events', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_event(request):
    events = Event.objects.filter(doctor=request.user).order_by('-date')
    template_data = dict(user=request.user, events=events,
        context_instance=RequestContext(request))

    return template_data


@login_required
@only_doctor
def add_event(request, template="cal/event/add.html"):
    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'doctor': request.user.id,
            'created_by': request.user.id,
            'date': datetime.now()
        })

        date = request.POST.get('date', None)
        if date:
            date = datetime.now().strptime(date, settings.DATE_FORMAT)
            request_params.update({'date': date})

        form = EventForm(request_params)

        if form.is_valid():
            form.save()
            return redirect(reverse("cal.list_event"))
        else:
            return render_to_response(template,
                {'form': form},
                context_instance=RequestContext(request))
    else:
        form = EventForm()

    return render_to_response(template, {'form': form},
                context_instance=RequestContext(request))


@login_required
@only_doctor
def edit_event(request, pk, template="cal/event/edit.html"):
    event = get_object_or_404(Event, pk=int(pk))

    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'doctor': request.user.id,
            'created_by': request.user.id,
        })

        date = request.POST.get('date', None)
        if date:
            date = datetime.now().strptime(date, settings.DATE_FORMAT)
            request_params.update({'date': date})

        form = EventForm(request_params, instance=event)

        if form.is_valid():
            form.save()
            return redirect(reverse("cal.list_event"))
        else:
            return render_to_response(template,
                {"form": form, 'event': event},
                context_instance=RequestContext(request))
    else:
        form = EventForm(instance=event)

    return render_to_response(template,
        {"form": form, 'event': event},
        context_instance=RequestContext(request))


@login_required
@only_doctor
def delete_event(request):
    if request.method == 'DELETE':
        data = json.loads(request.raw_post_data)
        pk = data['pk']

        event = get_object_or_404(Event, pk=int(pk))

        try:
            event.delete()
            return HttpResponse(json.dumps({'action': True}),
                status=200,
                mimetype='application/json')
        except:
            return HttpResponse(json.dumps({'action': False}),
                status=200,
                mimetype='application/json')
    else:
        return HttpResponse(json.dumps({'action': False}),
                status=200,
                mimetype='application/json')


@login_required()
def lookfor_patient(request, action=None, year=None, month=None, day=None):
    if action == 'info':
        pass
    elif action == 'new_app':
        if year and month and day:
            destination = 'cal.add'
        else:
            destination = 'cal.scheduler'
    elif action == 'list_app':
        destination = 'cal.app_list_patient'


    return render_to_response('cal/patient/lookfor_patient.html',
            {'destination':destination, 'year':year, 'month':month, 'day':day},
            context_instance=RequestContext(request))


@login_required()
def patient_searcher(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_administrative() or\
        logged_user_profile.is_doctor():
        data = {'ok': False}
        if request.method == 'POST':
            start = request.POST.get("start", "")

            if logged_user_profile.is_administrative():
                profiles = Profile.objects.filter(
                                Q(role__exact=settings.PATIENT),
                                Q(nif__istartswith=start)|
                                Q(name__istartswith=start)|
                                Q(first_surname__istartswith=start)|
                                Q(second_surname__istartswith=start)).order_by(
                                'name', 'first_surname', 'second_surname')
            else:
                doctor_user = logged_user_profile.user
                profiles = Profile.objects.filter(
                                Q(doctor=doctor_user,
                                role__exact=settings.PATIENT),
                                Q(nif__istartswith=start)|
                                Q(name__istartswith=start)|
                                Q(first_surname__istartswith=start)|
                                Q(second_surname__istartswith=start)).order_by(
                                'name', 'first_surname', 'second_surname')

            users =[]
            [users.append(profile.user) for profile in profiles]

            data = {'ok': True,
                    'completed_names':
                    [{'id': user.id,
                    'label':
                    (user.get_profile().get_full_name())}for user in users]
                    }
        return HttpResponse(simplejson.dumps(data))
    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def select_doctor(request, id_patient):
    patient_user = get_object_or_404(User, pk=int(id_patient))
    if request.method == 'POST':
        form = DoctorSelectionForm(request.POST)

        if form.is_valid():
            profile = patient_user.get_profile()
            profile.doctor = User.objects.get(pk=int(form.cleaned_data['doctor']))
            profile.save()
            if request.is_ajax():
                return HttpResponse('OK');
            return HttpResponseRedirect(reverse('cal.scheduler',
                args=[int(id_patient)]))
        elif request.is_ajax():
            return Http404
    else:
        form = DoctorSelectionForm()

    return render_to_response('cal/app/select_doctor.html', {'form': form,
        'patient_user': patient_user},
        context_instance=RequestContext(request))