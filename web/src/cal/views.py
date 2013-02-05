# -*- encoding: utf-8 -*-

from datetime import date, datetime, timedelta
from datetime import time as ttime
import time
import json
from itertools import chain
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _
from django.utils import simplejson
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.forms.util import ErrorList
from django.db.models.query import QuerySet


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
from cal.models import Payment

from cal.forms import SlotForm
from cal.forms import SlotTypeForm
from cal.forms import DoctorSelectionForm
from cal.forms import AppointmentForm
from cal.forms import VacationForm
from cal.forms import EventForm
from cal.forms import SchedulerForm
from cal.forms import PaymentForm
from cal.forms import PaymentFiltersForm

from cal.utils import create_calendar
from cal.utils import add_minutes
from cal.utils import get_weekday
from cal.utils import mnames
from cal.utils import get_doctor_preferences
from cal.utils import check_vacations
from cal.utils import check_scheduled_apps


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
@only_doctor_administrative
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
@only_doctor_administrative
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
@only_doctor_administrative
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
@only_doctor_administrative
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
@only_doctor_administrative
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
        birthdays=Profile.objects.filter(dob__month=month, dob__day=day),
        context_instance=RequestContext(request))

    return template_data

@login_required
@only_doctor_administrative
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
@only_doctor_administrative
def calendar_big(request, year, month, change='this', id_doctor=None):

    if change in ("next", "prev"):
        now, mdelta = date(int(year), int(month), 15), timedelta(days=31)

        if change == "next":
            mod = mdelta

        elif change == "prev":
            mod = -mdelta

        year, month = (now + mod).timetuple()[:2]

    doctors = Profile.objects.filter(role=settings.DOCTOR)
    if id_doctor:
        doctor = User.objects.get(pk=int(id_doctor))
        lst = create_calendar(int(year), int(month), doctor=doctor)
    else:
        doctor = None
        lst = create_calendar(int(year), int(month), doctor=request.user)
        if request.user.get_profile().is_administrative():
            for d in doctors:
                dlst = create_calendar(int(year), int(month), doctor=d.user)
                for i in range(len(lst)):
                    for j in range(len(lst[i])):
                        for k in range(len(lst[i][j])):
                            if isinstance(lst[i][j][k], list) and isinstance(dlst[i][j][k], list):
                                lst[i][j][k] += dlst[i][j][k]



    form = DoctorSelectionForm()

    return render_to_response('cal/includes/calendar_big.html', 
                                dict(year=year, month=month, doctors=doctors,
                                 doctor=doctor, month_days=lst, 
                                 mname=mnames[int(month) - 1], form = form),
        context_instance=RequestContext(request))


@login_required
@only_doctor_administrative
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
        birthdays=Profile.objects.filter(dob__month=month, dob__day=day),
        context_instance=RequestContext(request))

    return template_data


@login_required
@only_doctor_administrative
def app_add(request, year, month, day, id_user, check=False):
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
        sched_form = SchedulerForm(request.POST)
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

        if form.is_valid() and sched_form.is_valid():
            pre_save_instance = form.save(commit=False)
            available, free_intervals = Appointment.objects.availability(
                doctor,
                date(int(year), int(month), int(day)),
                pre_save_instance)

            if available and not check:
                form.save()
                if sched_form.is_valid():
                    number = sched_form.cleaned_data['number']
                    period = sched_form.cleaned_data['period']
                    interval = sched_form.cleaned_data['interval']
                    if number and period:
                        ok, conflicts = check_scheduled_apps(pre_save_instance, number, period, interval)
                        for app in ok:
                            app.pk = None
                            app.status = settings.RESERVED
                            app.save()

                if 'appointment' in request.session:
                    return redirect(reverse("consulting_main",
                        kwargs={'id_appointment':request.session['appointment'].id,
                            'code_illness':request.session['illness'].code}))
                else:
                    return redirect(reverse("cal.views.day",
                        args=(int(year), int(month), int(day), doctor.id)))
            else:
                error = False
                success = False
                conflicts = []
                msg = ''
                if not available:
                    error = True
                    msg = _(u'Conflicto de fecha y hora con otra cita. '\
                        'Por favor, seleccione un intervalo libre')
                elif sched_form.is_valid():
                    number = sched_form.cleaned_data['number']
                    period = sched_form.cleaned_data['period']
                    interval = sched_form.cleaned_data['interval']
                    if number and period:
                        ok, conflicts = check_scheduled_apps(pre_save_instance, number, period, interval)
                        if conflicts:
                            error = True
                            msg = _(u'La reserva de las siguientes citas presentan conflictos de disponibilidad en su agenda y no se crearán automáticamente' )
                        else:
                            msg = _(u'Es posible efectuar la reserva de las citas solicitadas' )
                            error = False
                            success = True

                return render_to_response("cal/app/add.html",
                    {'form': form,
                     'scheduler': sched_form,
                     'year': int(year), 'month': int(month), 'day': int(day),
                     'month_days': lst,
                     'mname': mname,
                     'doctor': doctor,
                     'patient_user': patient,
                     'conflicts': conflicts,
                     'doctor_preferences': doctor_preferences,
                     'free_intervals': free_intervals,
                     'not_available_error': error,
                     'successful_check': success,
                     'error_msg': msg},
                    context_instance=RequestContext(request))
        else:
            available, free_intervals = Appointment.objects.availability(
                doctor,
                date(int(year), int(month), int(day)))
    else:
        sched_form = SchedulerForm()
        form = AppointmentForm(user=doctor)
        available, free_intervals = Appointment.objects.availability(
            doctor,
            date(int(year), int(month), int(day)))
    if date(int(year), int(month), int(day)) < date.today():
        form = None

    return render_to_response("cal/app/add.html",
                {'form': form,
                 'scheduler': sched_form,
                 'year': int(year), 'month': int(month), 'day': int(day),
                 'month_days': lst,
                 'mname': mname,
                 'doctor': doctor,
                 'patient_user': patient,
                 'doctor_preferences': doctor_preferences,
                 'free_intervals': free_intervals},
                context_instance=RequestContext(request))


@login_required
@only_doctor_administrative
def app_edit(request, pk):
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
    available, free_intervals = Appointment.objects.availability(
            doctor,
            date(int(year), int(month), int(day)))

    doctor_preferences = get_doctor_preferences(year=year, month=month,
        day=day, doctor=doctor.id)

    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({
            'doctor': doctor.id,
            'created_by': request.user.id,
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
            year = int(pre_edit_instance.date.year)
            month = int(pre_edit_instance.date.month)
            day = int(pre_edit_instance.date.day)

            mname = mnames[int(month) - 1]

            lst = create_calendar(year, month, doctor=doctor)

            vacations = check_vacations(doctor, year, month, day)

            doctor_preferences = get_doctor_preferences(year=year, month=month,
                day=day, doctor=doctor.id)

            if vacations:
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
                                'vacations': vacations},
                        context_instance=RequestContext(request))

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
@only_doctor_administrative
def app_delete(request, pk):
    if request.method == 'DELETE':
        data = json.loads(request.raw_post_data)
        app_id = data['app_id']
        if int(app_id) != int(pk):
            raise Exception


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
@only_doctor_administrative
@paginate(template_name='cal/patient/list.html',
    list_name='events', objects_per_page=settings.OBJECTS_PER_PAGE)
def app_list_patient(request, id_patient):
    patient = get_object_or_404(User, pk=int(id_patient))
    events = Appointment.objects.filter(patient=patient).order_by('-date')

    template_data = dict(events=events, doctor=patient.get_profile().doctor,
                        patient=patient,
                        context_instance=RequestContext(request))

    return template_data

@login_required()
@only_doctor_administrative
@paginate(template_name='cal/patient/list.html',
    list_name='events', objects_per_page=settings.OBJECTS_PER_PAGE)
def get_appointments(request, year, month, day):
    logged_user_profile = request.user.get_profile()

    #patient_user_id = request.session['patient_user_id']
    
    appointments = Appointment.objects.filter(date__year=int(year), date__month=int(month), date__day=int(day)).order_by('-start_time')
    
    template_data = {}
    template_data.update({'events': appointments})
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
@only_doctor_administrative
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
@only_doctor_administrative
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
@only_doctor_administrative
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
@only_doctor_administrative
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
@only_doctor_administrative
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

            data = {'ok': True,
                    'completed_names':
                    [{'id': profile.user.id,
                    'label':
                    (profile.get_full_name()+ ' ['+profile.nif+']')}for profile in profiles]
                    }
        return HttpResponse(simplejson.dumps(data))
    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@only_doctor_administrative
def select_doctor(request, id_patient):
    patient_user = get_object_or_404(User, pk=int(id_patient))
    if request.method == 'POST':
        form = DoctorSelectionForm(request.POST)

        if form.is_valid():
            profile = patient_user.get_profile()
            check_transfer(request, id_patient, True)
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

@login_required()
@only_doctor_administrative
def check_transfer(request, id_patient, doit=False):
    if request.method == 'POST':
        id_doctor = request.POST.get('doctor',None)
    else:
        return Http404
    transferable, moves = True, 0
    patient_user = get_object_or_404(User, pk=int(id_patient))
    doctor = get_object_or_404(User, pk=int(id_doctor))
    next_apps = Appointment.objects.filter(patient=patient_user,
                            date__gt=date.today()).order_by(
                            'date')
    for app in next_apps:
        available, free_intervals = Appointment.objects.availability(
                doctor, app.date, app)
        transferable = available
        if not available and free_intervals:
            for i in free_intervals:
                if i['duration'] >= app.duration:
                    moves += 1
                    transferable = True
                    if doit:
                        app.start_time = i['start_time']
                        app.end_time = add_minutes(i['start_time'], app.duration)
                    break
        if doit:
            if transferable:
                app.doctor = doctor
                #app.description = "%s %s"%(app.app_type.description, app.description)
                #app.app_type = None
                app.save()
            else:
                app.delete()
    data = {'ok': transferable,
            'moves': moves}
    if doit:
        return 1
    else:
        return HttpResponse(simplejson.dumps(data))

@login_required
@only_doctor_administrative
@paginate(template_name='cal/payment/list_ajax.html',
    list_name='events', objects_per_page=settings.OBJECTS_PER_PAGE*2)
def get_payment_list(request, query_filter=None):
    apps = Appointment.objects.all().order_by('-date')
    if query_filter:
        apps = apps.filter(query_filter)
    elif request.user.get_profile().is_doctor():
        apps = apps.filter(doctor=request.user)

    queries_without_page = request.GET.copy()
    if queries_without_page.has_key('page'):
        del queries_without_page['page']

    template_data = dict(user=request.user, 
                        events=apps, 
                        queries=queries_without_page,
                        context_instance=RequestContext(request))
    return template_data

@login_required
@only_doctor_administrative
def payment_list(request):
    form = PaymentFiltersForm()
    if request.method == "GET":
        form = PaymentFiltersForm(request.GET, user=request.user)
        query_filter = Q()
        exclude_filter = Q()
        for k, v in request.GET.items():
            if not v:
                continue
            if k.startswith('app_date'):
                day, month, year  = v.split('/')
                if k.endswith('0'):
                    query_filter = query_filter & Q(date__gte=date(int(year),
                                                                int(month),
                                                                int(day)))
                else:
                    query_filter = query_filter & Q(date__lte=date(int(year),
                                                                int(month),
                                                                int(day)))
            elif k.startswith('payment_date'):
                day, month, year  = v.split('/')
                if k.endswith('0'):
                    query_filter = query_filter \
                            & Q(payment_appointment__date__gte=date(int(year),
                                                                int(month),
                                                                int(day)))
                else:
                    query_filter = query_filter \
                            & Q(payment_appointment__date__lte=date(int(year),
                                                                int(month),
                                                                int(day)))
            elif k.startswith('value'):
                if k.endswith('0'):
                    query_filter = query_filter \
                            & Q(payment_appointment__value__gte=Decimal(v))
                else:
                    query_filter = query_filter \
                            & Q(payment_appointment__value__lte=Decimal(v))
            elif k.startswith('discount'):
                if k.endswith('0'):
                    query_filter = query_filter \
                            & Q(payment_appointment__discount__gte=int(v))
                else:
                    query_filter = query_filter \
                            & Q(payment_appointment__discount__lte=int(v))
            elif k.startswith('method'):
                query_filter = query_filter \
                    | Q(payment_appointment__method__in=request.GET.getlist(k))
            elif k.startswith('patient'):
                query_filter = query_filter \
                    & Q(patient__id__in=request.GET.getlist(k))
            elif k.startswith('doctor'):
                query_filter = query_filter \
                    & Q(doctor__id__in=request.GET.getlist(k))
            elif k.startswith('status'):
                subquery = Q()
                for op in request.GET.getlist(k):
                    if int(op)==0:
                        subquery = subquery \
                        | Q(payment_appointment__method__gte=0)
                    elif int(op)==1:
                        subquery = subquery \
                            | (Q(status=settings.CONFIRMED) \
                            & Q(date__gte=date.today()))
                    elif int(op)==2:
                        subquery = subquery \
                                    | Q(status=settings.CONFIRMED) \
                                    & Q(appointment_conclusions__id__gt=0) \
                                    & Q(payment_appointment__isnull=True)
                    elif int(op)==3:
                        subquery = subquery \
                                    | Q(status=settings.RESERVED) \
                                    & Q(date__gte=date.today())
                    elif int(op)==4:
                        subquery = subquery \
                                    | Q(status=settings.CANCELED_BY_DOCTOR) \
                                    | Q(status=settings.CANCELED_BY_PATIENT)
                    elif int(op)==5:
                        subquery = subquery \
                                    | Q(status=settings.RESERVED) \
                                    & Q(date__lt=date.today())
                    elif int(op)==6:
                        subquery = subquery \
                                    | Q(status=settings.CONFIRMED) \
                                    & Q(appointment_conclusions__isnull=True) \
                                    & Q(appointment_tasks__isnull=True) \
                                    & Q(date__lt=date.today())
                query_filter = query_filter & subquery
        if request.is_ajax():       
            return get_payment_list(request, query_filter)

    return render_to_response('cal/payment/list.html', {'form': form},
        context_instance=RequestContext(request))


@login_required
@only_doctor_administrative
def payment_edit(request, id_appointment):
    app = get_object_or_404(Appointment, pk=int(id_appointment))
    payment = None
    try:
        payment = Payment.objects.get(appointment=app)
        form = PaymentForm(instance=payment)
    except:
        form = PaymentForm()
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if payment:
            form = PaymentForm(request.POST, instance=payment)
        if form.is_valid():
            payment = form.save(commit=False)
            payment.created_by = request.user
            payment.appointment = app
            payment.save()
            return HttpResponseRedirect(reverse('cal.list_payment'))

    return render_to_response('cal/payment/edit.html', {'form': form,
        'app': app},
        context_instance=RequestContext(request))