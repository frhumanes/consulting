# -*- encoding: utf-8 -*-
import time
from datetime import time as ttime
from datetime import date, timedelta, datetime

from random import randint

from decorators import paginate
from decorators import only_doctor_consulting

from django.middleware.csrf import get_token
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import send_mail

from userprofile.models import Profile
from medicament.models import Component, Group
from consulting.models import Medicine, Task, Conclusion, Result
from cal.models import Appointment, Slot, SlotType
from illness.models import Illness
from survey.models import Survey, Option

from userprofile.forms import ProfileForm, ProfileSurveyForm
from consulting.forms import MedicineForm, ConclusionForm, ActionSelectionForm
from illness.forms import IllnessSelectionForm, IllnessAddPatientForm
from survey.forms import SelectSurveyForm, QuestionsForm
from cal.forms import AppointmentForm

from consulting.helper import strip_accents

from cal.utils import create_calendar
from cal.utils import mnames
from cal.utils import check_vacations
from cal.utils import get_doctor_preferences
from cal.utils import add_minutes


#################################### INDEX ####################################
@login_required()
def index(request):

    logged_user_profile = request.user.get_profile()

    if logged_user_profile.role == settings.DOCTOR:

        return render_to_response('consulting/doctor/index_doctor.html', {},
                                context_instance=RequestContext(request))
    elif logged_user_profile.role == settings.ADMINISTRATIVE:
        return render_to_response(
                    'consulting/administrative/index_administrative.html', {},
                    context_instance=RequestContext(request))
    elif logged_user_profile.role == settings.PATIENT:
        return render_to_response('consulting/patient/index_patient.html', {},
                                context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


################################# CONSULTATION ################################
@login_required
@only_doctor_consulting
def select_year_month(request, id_patient, year=None):
    patient = get_object_or_404(User, pk=int(id_patient))
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

    data = dict(years=lst, user=request.user, year=year, today=today,
                patient=patient)

    return render_to_response("consulting/consultation/select_year_month.html",
                                data,
                                context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def today(request):
    year, month, day = time.localtime()[:3]

    return HttpResponseRedirect(reverse('consulting_day',
                                        args=[year, month, day]))


@login_required
@only_doctor_consulting
@paginate(template_name='consulting/consultation/list.html',
    list_name='events', objects_per_page=settings.OBJECTS_PER_PAGE)
def day(request, year, month, day):
    doctor = request.user
    vacations = check_vacations(doctor, year, month, day)

    if not vacations:
        events = Appointment.objects.filter(doctor=doctor, date__year=year,
            date__month=month, date__day=day).order_by('start_time')
    else:
        events = Appointment.objects.none()

    lst = create_calendar(int(year), int(month), doctor=request.user)

    available, free_intervals = Appointment.objects.availability(
                doctor,
                date(int(year), int(month), int(day)))

    template_data = dict(year=year, month=month, day=day,
        user=request.user, month_days=lst, mname=mnames[int(month) - 1],
        events=events, free_intervals=free_intervals,
        context_instance=RequestContext(request))

    return template_data


@login_required
@only_doctor_consulting
@paginate(template_name='consulting/consultation/list_day_new_app.html',
    list_name='events', objects_per_page=settings.OBJECTS_PER_PAGE)
def day_new_app(request, year, month, day, id_patient):
    patient = get_object_or_404(User, pk=int(id_patient))
    doctor = request.user
    vacations = check_vacations(doctor, year, month, day)

    if not vacations:
        events = Appointment.objects.filter(doctor=doctor, date__year=year,
            date__month=month, date__day=day).order_by('start_time')
    else:
        events = Appointment.objects.none()

    lst = create_calendar(int(year), int(month), doctor=request.user)

    available, free_intervals = Appointment.objects.availability(
                doctor,
                date(int(year), int(month), int(day)))

    template_data = dict(year=year, month=month, day=day,
        user=request.user, month_days=lst, mname=mnames[int(month) - 1],
        events=events, free_intervals=free_intervals, patient=patient,
        context_instance=RequestContext(request))

    return template_data


@login_required
@only_doctor_consulting
def month(request, year, month, change=None):
    year, month = int(year), int(month)

    if change in ("next", "prev"):
        now, mdelta = date(year, month, 15), timedelta(days=31)

        if change == "next":
            mod = mdelta

        elif change == "prev":
            mod = -mdelta

        year, month = (now + mod).timetuple()[:2]

    lst = create_calendar(year, month, doctor=request.user)
    return render_to_response("consulting/consultation/month.html",
        dict(year=year, month=month, user=request.user,
            month_days=lst, mname=mnames[month - 1]),
            context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def month_new_app(request, year, month, change, id_patient):
    patient = get_object_or_404(User, pk=int(id_patient))
    year, month = int(year), int(month)

    if change in ("next", "prev"):
        now, mdelta = date(year, month, 15), timedelta(days=31)

        if change == "next":
            mod = mdelta

        elif change == "prev":
            mod = -mdelta

        year, month = (now + mod).timetuple()[:2]

    lst = create_calendar(year, month, doctor=request.user)
    return render_to_response("consulting/consultation/month_new_app.html",
        dict(year=year, month=month, user=request.user,
            month_days=lst, mname=mnames[month - 1], patient=patient),
            context_instance=RequestContext(request))


@login_required
def app_add(request, year, month, day, id_patient):
    patient = get_object_or_404(User, pk=int(id_patient))
    doctor = request.user
    lst = create_calendar(int(year), int(month), doctor=doctor)

    # vacations = check_vacations(doctor, year, month, day)

    # if vacations:
    #     return render_to_response("cal/app/edit.html",
    #             {'vacations': vacations,
    #              'year': int(year), 'month': int(month), 'day': int(day),
    #              'month_days': lst,
    #              'doctor': doctor,
    #              'patient': patient,
    #              'not_available_error': True,
    #              'error_msg': _('Appointment can not be set. '\
    #                 'Please, choose another time interval')},
    #             context_instance=RequestContext(request))

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
                    duration = (datetime.combine(date.today(), end_time) - \
                        datetime.combine(date.today(), start_time)).seconds
                    del request_params['app_type']
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

                return redirect(reverse("consulting_day_new_app",
                        args=(int(year), int(month), int(day), patient.id)))
            else:
                return render_to_response("consulting/consultation/new_app.html",
                    {'form': form,
                     'year': int(year), 'month': int(month), 'day': int(day),
                     'month_days': lst,
                     'mname': mname,
                     'doctor': doctor,
                     'patient': patient,
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
    return render_to_response("consulting/consultation/new_app.html",
                {'form': form,
                 'year': int(year), 'month': int(month), 'day': int(day),
                 'month_days': lst,
                 'mname': mname,
                 'doctor': doctor,
                 'patient': patient,
                 'doctor_preferences': doctor_preferences,
                 'free_intervals': free_intervals},
                context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def select_illness(request, id_appointment):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    if request.method == 'POST':
        form = IllnessSelectionForm(request.POST,
                                    id_appointment=appointment.id)
        if form.is_valid():
            id_illness = form.cleaned_data['illness']
            if id_illness == str(settings.DEFAULT_ILLNESS):
                return HttpResponseRedirect(reverse('consulting_select_action',
                                            args=[id_appointment]))
            else:
                print 'NO ES POR DEFECTO'
                pass
    else:
        form = IllnessSelectionForm(id_appointment=appointment.id)
    return render_to_response('consulting/consultation/select_illness.html',
                                {'form': form,
                                'patient_user': appointment.patient,
                                'id_appointment': id_appointment},
                                context_instance=RequestContext(request))


def task_completed(id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    if task.task_results.all():
        result = task.task_results.latest('date')
        options_result = result.options.all()

        blocks = result.survey.blocks.all().order_by('code')
        completed_block = True
        for block in blocks:
            if not completed_block:
                break
            categories = block.categories.all().order_by('code')
            completed_category = True
            for category in categories:
                if not completed_category:
                    break
                questions = category.categories_questions.all().order_by('id')
                completed_question = True
                for question in questions:
                    if not completed_question:
                        break
                    options = question.question_options.all().order_by('id')

                    for option in options:
                        if option  in options_result:
                            completed_question = True
                            completed_category = True
                            completed_block = True
                            break
                        else:
                            completed_question = False
                            completed_category = False
                            completed_block = False
        return completed_block
    else:
        return False


@login_required
@only_doctor_consulting
def select_action(request, id_appointment):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    if request.method == 'POST':
        form = ActionSelectionForm(request.POST)
        if form.is_valid():
            action = form.cleaned_data['action']
            if action == str(settings.CONCLUSION):
                return HttpResponseRedirect(reverse('consulting_conclusion',
                                            args=[id_appointment]))
            else:
                survey = Survey.objects.get(id=settings.DEFAULT_ILLNESS)

                tasks_with_survey = Task.objects.filter(
                                        patient=appointment.patient,
                                        survey=survey)
                if tasks_with_survey:
                    last_task_with_survey = tasks_with_survey.latest(
                                                            'creation_date')
                    if not task_completed(last_task_with_survey.id):
                        return HttpResponseRedirect(
                                reverse('consulting_administrative_data',
                                        args=[last_task_with_survey.id]))
                task = Task(created_by=request.user,
                    patient=appointment.patient, survey=survey,
                    appointment=appointment, self_administered=False)
                task.save()
                return HttpResponseRedirect(
                                reverse('consulting_administrative_data',
                                        args=[task.id]))
    else:
        form = ActionSelectionForm()
    return render_to_response('consulting/consultation/select_action.html',
                                {'form': form,
                                'patient_user': appointment.patient,
                                'id_appointment': id_appointment},
                                context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def conclusion(request, id_appointment, id_result=None):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))

    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({'created_by': request.user.id})
        form = ConclusionForm(request_params)
        if form.is_valid():
            conclusion = form.save(commit=False)
            conclusion.patient = appointment.patient
            conclusion.appointment = appointment
            conclusion.save()
            if id_result:
                result = get_object_or_404(Result, pk=int(id_result))
                conclusion.result = result
                conclusion.save()

                if result.survey.code == 1 or result.survey.code == 2:
                    return HttpResponseRedirect(
                        reverse('consulting_add_illness_patient',
                                args=[conclusion.id]))
                else:
                    return HttpResponseRedirect(
                                reverse('consulting_new_medicine_conclusion',
                                        args=[conclusion.id]))
            else:
                return HttpResponseRedirect(
                                reverse('consulting_new_medicine_conclusion',
                                        args=[conclusion.id]))
    else:
        form = ConclusionForm()

    return render_to_response('consulting/consultation/conclusion.html',
                                {'form': form,
                                'patient_user': appointment.patient,
                                'id_appointment': id_appointment,
                                'id_result': id_result},
                                context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def new_medicine_conclusion(request, id_conclusion):
    conclusion = get_object_or_404(Conclusion, pk=int(id_conclusion))
    patient = conclusion.patient

    if request.method == "POST":
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({'created_by': request.user.id})
        form = MedicineForm(request_params)
        if form.is_valid():
            # COMPONENT CAN BE NEW OR ALREADY EXISTED
            component_name = form.cleaned_data['searcher_component']
            kind_component = form.cleaned_data['kind_component']
            try:
                component = Component.objects.get(name=component_name,
                            kind_component=kind_component)
            except Component.DoesNotExist:
                component_group = Group.objects.get(id=-1)
                component = Component(name=component_name,
                                    kind_component=kind_component)
                component.save()
                component.groups.add(component_group)
                component.save()
            medicine = form.save(commit=False)
            medicine.component = component
            medicine.patient = patient
            medicine.conclusion = conclusion
            medicine.save()

            return HttpResponseRedirect(
                                reverse('consulting_new_medicine_conclusion',
                                args=[id_conclusion]))
    else:
        form = MedicineForm()

    return render_to_response(
                'consulting/consultation/new_medicine.html',
                {'form': form,
                'id_conclusion': id_conclusion,
                'patient_user': patient},
                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
@paginate(
    template_name='consulting/consultation/list_medicines.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_medicines_before_conclusion(request, id_conclusion):
    conclusion = get_object_or_404(Conclusion, pk=int(id_conclusion))

    medicines = conclusion.conclusion_medicines.filter(
        before_after_first_appointment=settings.BEFORE).order_by('-date')
    template_data = {}
    template_data.update({'patient_user': conclusion.patient,
                        'medicines': medicines,
                        'id_conclusion': id_conclusion,
                        'csrf_token': get_token(request)})
    return template_data


@login_required()
@only_doctor_consulting
@paginate(
    template_name='consulting/consultation/list_medicines.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_medicines_after_conclusion(request, id_conclusion):
    conclusion = get_object_or_404(Conclusion, pk=int(id_conclusion))

    medicines = conclusion.conclusion_medicines.filter(
        before_after_first_appointment=settings.AFTER).order_by('-date')

    template_data = {}
    template_data.update({'patient_user': conclusion.patient,
                        'medicines': medicines,
                        'id_conclusion': id_conclusion,
                        'csrf_token': get_token(request)})
    return template_data


@login_required()
@only_doctor_consulting
def detail_medicine_conclusion(request):
    if request.method == 'POST':
        medicine_id = request.POST.get("medicine_id", "")
        id_conclusion = request.POST.get("id_conclusion", "")
        try:
            medicine = Medicine.objects.get(id=medicine_id)
            conclusion = get_object_or_404(Conclusion, pk=int(id_conclusion))
            return render_to_response(
                        'consulting/consultation/detail_medicine.html',
                        {'medicine': medicine,
                        'id_conclusion': conclusion.id},
                        context_instance=RequestContext(request))
        except Medicine.DoesNotExist:
                return HttpResponseRedirect(reverse('consulting_index'))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@only_doctor_consulting
@paginate(template_name='consulting/consultation/list_medicines_ajax.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def remove_medicine_conclusion(request):
    if request.method == 'POST':
        medicine_id = request.POST.get("medicine_id", "")
        id_conclusion = request.POST.get("id_conclusion", "")
        try:
            medicine = Medicine.objects.get(id=medicine_id)
            when = medicine.before_after_first_appointment
            medicine.delete()

            conclusion = get_object_or_404(Conclusion, pk=int(id_conclusion))

            if when == settings.BEFORE:
                medicines = conclusion.conclusion_medicines.filter(
                        before_after_first_appointment=settings.BEFORE).\
                        order_by('-date')
            else:
                medicines = conclusion.conclusion_medicines.filter(
                        before_after_first_appointment=settings.AFTER).\
                        order_by('-date')

            template_data = {}
            template_data.update({'medicines': medicines,
                                    'id_conclusion': id_conclusion})
            return template_data
        except Medicine.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@only_doctor_consulting
def add_illness_patient(request, id_conclusion):
    conclusion = get_object_or_404(Conclusion, pk=int(id_conclusion))
    patient = conclusion.patient
    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())

        request_params.update({'created_by': request.user.id})
        request_params.update({'illnesses': request.POST.getlist('illnesses')})

        form = IllnessAddPatientForm(request_params,
                                    instance=patient.get_profile())
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(
                                    reverse('consulting_add_illness_patient',
                                    args=[id_conclusion]))
    else:
        form = IllnessAddPatientForm(instance=patient.get_profile())
    return render_to_response(
                        'consulting/consultation/add_illness_patient.html',
                        {'form': form,
                        'id_conclusion': id_conclusion,
                        'patient_user': patient},
                        context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def select_survey(request, id_conclusion):
    conclusion = get_object_or_404(Conclusion, pk=int(id_conclusion))
    patient = conclusion.patient
    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())

        request_params.update({'created_by': request.user.id})

        form = SelectSurveyForm(request_params)
        if form.is_valid():

            id_survey = form.cleaned_data['survey']
            survey = get_object_or_404(Survey, pk=int(id_survey))
            print '-----------------------'
            print survey

            task = Task(created_by=request.user,
                        patient=patient, survey=survey,
                        appointment=conclusion.appointment,
                        self_administered=False)
            task.save()

            if survey.code == 1:
                print '---SE VA A REALIZAR UN ESTUDIO PREVIO---'
            elif survey.code == 3:
                print '---SE VA A REALIZAR A/D EXTENSO---'
            else:
                print '---SE VA A REALIZAR A/D ABREVIADO---'

    else:
        form = SelectSurveyForm()
    return render_to_response(
                        'consulting/consultation/select_survey.html',
                        {'form': form,
                        'id_conclusion': id_conclusion,
                        'patient_user': patient},
                        context_instance=RequestContext(request))


def new_result_sex_status(id_logged_user, id_task):
    logged_user = get_object_or_404(User, pk=int(id_logged_user))
    task = get_object_or_404(Task, pk=int(id_task))
    profile = task.patient.get_profile()

    #NEW RESULT)
    result = Result(patient=task.patient,
                    survey=task.survey,
                    task=task,
                    created_by=logged_user)
    result.save()

    #SEX
    if profile.sex == settings.WOMAN:
        sex_option = get_object_or_404(Option, code='DA4.1')
    else:
        sex_option = get_object_or_404(Option, code='DA4.0')

    #STATUS
    status = profile.status
    if status == settings.MARRIED:
        status_option = get_object_or_404(Option, code='DA9.1')
    elif status == settings.STABLE_PARTNER:
        status_option = get_object_or_404(Option, code='DA9.2')
    elif status == settings.DIVORCED:
        status_option = get_object_or_404(Option, code='DA9.3')
    elif status == settings.WIDOW_ER:
        status_option = get_object_or_404(Option, code='DA9.4')
    elif status == settings.SINGLE:
        status_option = get_object_or_404(Option, code='DA9.5')
    elif status == settings.OTHER:
        status_option = get_object_or_404(Option, code='DA9.6')

    #UPDATE RESULT
    result.options.add(sex_option)
    result.options.add(status_option)
    result.save()

    return result


@login_required()
@only_doctor_consulting
def administrative_data(request, id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    user = task.patient
    profile = user.get_profile()

    # CHECK IF DOCTOR CONTAINS THIS PATIENT
    if not user in request.user.get_profile().patients.all():
        return HttpResponseRedirect(reverse('consulting_index'))

    if request.method == "POST":
        exclude_list = ['user', 'role', 'doctor', 'patients',
                            'username', 'illnesses']

        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({'created_by': request.user.id})

        form = ProfileSurveyForm(request_params, instance=profile,
                            exclude_list=exclude_list)

        #Field to username
        name = profile.name
        first_surname = profile.first_surname
        nif = profile.nif
        dob = profile.dob

        if form.is_valid():
            ######################## ACTIVE USER ######################
            if format_string(form.cleaned_data['active']) == '1':
                user.is_active = True
            else:
                user.is_active = False
            user.save()
            ###########################################################
            profile = form.save(commit=False)
            if not form.cleaned_data['postcode']:
                profile.postcode = None

            #Automatic to format name, first_surname and
            #second_surname
            profile.name = format_string(form.cleaned_data['name'])
            profile.first_surname = format_string(
                            form.cleaned_data['first_surname'])
            profile.second_surname = format_string(
                            form.cleaned_data['second_surname'])

            #######################CHECK USERNAME #####################
            #NUEVO USERNAME si se ha modificado el nombre o el
            #primer apellido o el nif, o si ahora el nif está vacío y
            #se ha modificado la fecha de nacimiento
            name_form = form.cleaned_data['name']
            first_surname_form = form.cleaned_data['first_surname']
            nif_form = form.cleaned_data['nif']
            dob_form = form.cleaned_data['dob']

            if (name != name_form or\
                first_surname != first_surname_form or\
                nif != nif_form) or\
                (nif_form == '' and dob != dob_form):
                #NUEVO username
                username = generate_username(form)
                profile.user.username = username
                profile.user.save()
                profile.username = username

                profile.save()

                result = new_result_sex_status(request.user.id, task.id)

                #SEN EMAIL to warn new username
                sendemail(user)

                return render_to_response(
                                    'consulting/consultation/warning.html',
                                    {'patient_user': user,
                                    'id_result': result.id},
                                    context_instance=RequestContext(request))
            else:
                profile.save()
                last_result = []
                if task.task_results.all():
                    last_result = task.task_results.latest('date')
                result = new_result_sex_status(request.user.id, task.id)

                if last_result:
                    options = last_result.options.all()
                    add_options = options.exclude(code__istartswith='DA')
                    result.options.add(*add_options)
                return HttpResponseRedirect(reverse('consulting_risk',
                                                    args=[result.id]))
        else:
            return render_to_response(
                            'consulting/consultation/administrative_data.html',
                            {'form': form,
                            'patient_user': user,
                            'task': task},
                            context_instance=RequestContext(request))
    else:
        exclude_list = ['user', 'role', 'doctor', 'patients', 'username',
                        'illnesses']

        if user.is_active:
            active = settings.ACTIVE
        else:
            active = settings.DEACTIVATE

        form = ProfileSurveyForm(instance=profile, exclude_list=exclude_list,
                            initial={'active': active})

    return render_to_response('consulting/consultation/administrative_data.html',
                            {'form': form,
                            'patient_user': user,
                            'task': task},
                            context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def risk(request, id_result):
    result = get_object_or_404(Result, pk=int(id_result))
    block = result.survey.blocks.all()[1]
    name_block = block.name
    categories = block.categories.all().order_by('id')

    dic = {}
    for category in categories:
        questions = category.categories_questions.all().order_by('id')
        for question in questions:
            options = question.question_options.all().order_by('id')
            dic[question.id] = [(option.id, option.text)for option in options]

    if request.method == 'POST':
        form = QuestionsForm(request.POST, dic=dic,
                                        selected_options=result.options.all())

        if form.is_valid():
            items = form.cleaned_data.items()
            for name_field, values_list in items:
                if values_list:
                    for value in values_list:
                        option = get_object_or_404(Option, pk=int(value))
                        result.options.add(option)
                        result.save()
    else:
        form = QuestionsForm(dic=dic, selected_options=result.options.all())

    return render_to_response('consulting/consultation/risk.html',
                            {'form': form,
                            'result': result,
                            'name_block': name_block,
                            'patient_user': result.patient},
                            context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def new_medicine_survey(request, id_result):
    result = get_object_or_404(Result, pk=int(id_result))
    patient = result.patient
    if request.method == "POST":
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update(
                            {'created_by': request.user.id,
                            'before_after_first_appointment': settings.BEFORE})

        form = MedicineForm(request_params)
        if form.is_valid():
            # COMPONENT CAN BE NEW OR ALREADY EXISTED
            component_name = form.cleaned_data['searcher_component']
            kind_component = form.cleaned_data['kind_component']
            try:
                component = Component.objects.get(name=component_name,
                            kind_component=kind_component)
            except Component.DoesNotExist:
                component_group = Group.objects.get(id=-1)
                component = Component(name=component_name,
                                    kind_component=kind_component)
                component.save()
                component.groups.add(component_group)
                component.save()
            medicine = form.save(commit=False)
            medicine.component = component
            medicine.patient = patient
            medicine.result = result
            medicine.save()

            return HttpResponseRedirect(
                                reverse('consulting_new_medicine_survey',
                                args=[id_result]))
    else:
        form = MedicineForm()
    return render_to_response(
                'consulting/consultation/new_medicine_survey.html',
                {'form': form,
                'id_appointment': result.task.appointment.id,
                'id_result': id_result,
                'patient_user': patient},
                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
@paginate(
    template_name='consulting/consultation/list_medicines_survey.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_medicines_before_survey(request, id_result):
    result = get_object_or_404(Result, pk=int(id_result))

    medicines = result.result_medicines.filter(
                            before_after_first_appointment=settings.BEFORE).\
                            order_by('-date')

    template_data = {}
    template_data.update({'patient_user': result.patient,
                        'medicines': medicines,
                        'id_appointment': result.task.appointment.id,
                        'id_result': id_result,
                        'csrf_token': get_token(request)})
    return template_data


@login_required()
@only_doctor_consulting
def detail_medicine_survey(request):
    if request.method == 'POST':
        medicine_id = request.POST.get("medicine_id", "")
        id_result = request.POST.get("id_result", "")
        try:
            medicine = Medicine.objects.get(id=medicine_id)
            return render_to_response(
                        'consulting/consultation/detail_medicine.html',
                        {'medicine': medicine,
                        'id_result': id_result},
                        context_instance=RequestContext(request))
        except Medicine.DoesNotExist:
                return HttpResponseRedirect(reverse('consulting_index'))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@only_doctor_consulting
@paginate(template_name='consulting/consultation/list_medicines_ajax_survey.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def remove_medicine_survey(request):
    if request.method == 'POST':
        medicine_id = request.POST.get("medicine_id", "")
        id_result = request.POST.get("id_result", "")
        try:
            medicine = Medicine.objects.get(id=medicine_id)
            when = medicine.before_after_first_appointment
            medicine.delete()

            result = get_object_or_404(Result, pk=int(id_result))

            if when == settings.BEFORE:
                medicines = result.result_medicines.filter(
                        before_after_first_appointment=settings.BEFORE).\
                        order_by('-date')
            else:
                medicines = result.result_medicines.filter(
                        before_after_first_appointment=settings.AFTER).\
                        order_by('-date')

            template_data = {}
            template_data.update({'medicines': medicines,
                                    'id_result': id_result})
            return template_data
        except Medicine.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


################################### PATIENT ###################################
def format_string(string):
    string_lower = string.lower()
    string_split = string_lower.split()

    len_string_split = len(string_split)

    if len_string_split > 1:
        cont = 0
        while(cont < len_string_split):
            string_split[cont] = string_split[cont].capitalize()
            cont = cont + 1
        new_string = ' '.join(string_split)
    else:
        new_string = string_lower.capitalize()
    return new_string


def generate_username(form):
    name = format_string(strip_accents(form.cleaned_data['name']))

    LEN_NIF = -3
    split_name = name.lower().split()
    first_letter = split_name[0][0]
    second_letter = ''
    first_surname = format_string(
                        strip_accents(form.cleaned_data['first_surname']))

    if first_surname.find(' ') != -1:
        first_surname = first_surname.replace(' ', '')

    if len(split_name) > 1:
        last_position = len(split_name) - 1
        second_letter = split_name[last_position][0]

    nif = form.cleaned_data['nif']
    if not nif:
        dob = form.cleaned_data['dob']
        code = str(dob.strftime('%d%m'))
        username = first_letter + second_letter + first_surname.lower() +\
                    code
        while Profile.objects.filter(username=username).count() > 0:
            code = str(randint(0, 9999))
            username = first_letter + second_letter + first_surname.lower() +\
                    code
    else:
        code = nif[LEN_NIF:]
        username = first_letter + second_letter + first_surname.lower() +\
                    code
    return username


def sendemail(user):
    subject = render_to_string(
                            'registration/identification_email_subject.txt',
                            {})
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    message = render_to_string(
                            'registration/identification_email_message.txt',
                            {'username': user.username,
                            'password': settings.DEFAULT_PASSWORD})

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


@login_required()
def newpatient(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor() or\
        logged_user_profile.is_administrative():
        same_username = False

        if request.method == "POST":
            if logged_user_profile.is_doctor():
                    exclude_list = ['user', 'role', 'doctor', 'patients',
                                    'username']
            else:
                exclude_list = ['user', 'role', 'doctor', 'patients',
                                'username', 'sex', 'status', 'profession']
            request_params = dict([k, v] for k, v in request.POST.items())
            request_params.update({'created_by': request.user.id})
            form = ProfileForm(request_params, exclude_list=exclude_list)
            if form.is_valid():
                username = generate_username(form)
                try:
                    Profile.objects.get(username=username)
                    same_username = True
                except Profile.DoesNotExist:
                    ############################USER###########################
                    user = User.objects.create_user(username=username,
                        password=settings.DEFAULT_PASSWORD,
                        email=form.cleaned_data['email'])
                    user.first_name = format_string(form.cleaned_data['name'])
                    user.last_name = format_string(
                                        form.cleaned_data['first_surname'])\
                                        + ' ' +\
                                format_string(
                                        form.cleaned_data['second_surname'])
                    user.email = form.cleaned_data['email']
                    user.save()
                    ##########################PROFILE##########################
                    try:
                        profile = form.save(commit=False)
                        #Automatic to format name, first_surname and
                        #second_surname
                        profile.name = format_string(form.cleaned_data['name'])
                        profile.first_surname = format_string(
                                        form.cleaned_data['first_surname'])
                        profile.second_surname = format_string(
                                        form.cleaned_data['second_surname'])

                        profile.username = username
                        profile.role = settings.PATIENT
                        if not form.cleaned_data['postcode']:
                            profile.postcode = None
                        #Relationships between patient and doctor
                        if logged_user_profile.is_doctor():
                            profile.doctor = logged_user_profile.user
                        profile.user = user
                        profile.save()
                        default_illness = Illness.objects.get(
                                                id=settings.DEFAULT_ILLNESS)
                        profile.illnesses.add(default_illness)
                        profile.save()

                        #Relationships between doctor and her/his patients
                        if logged_user_profile.is_doctor():
                            logged_user_profile.patients.add(user)
                            logged_user_profile.save()
                    except Exception:
                        user.delete()
                        return HttpResponseRedirect(
                                                reverse('consulting_index'))
                    ###########################################################
                    #SEND EMAIL
                    sendemail(user)

                    return render_to_response(
                            'consulting/patient/patient_identification.html',
                            {'patient_user': user,
                            'newpatient': True},
                            context_instance=RequestContext(request))
        else:
            if logged_user_profile.is_doctor():
                exclude_list = ['user', 'role', 'doctor', 'patients',
                                'username']
            else:
                exclude_list = ['user', 'role', 'doctor', 'patients',
                                'username', 'sex', 'status', 'profession']
            form = ProfileForm(exclude_list=exclude_list)

        return render_to_response('consulting/patient/patient.html',
                                    {'form': form,
                                    'same_username': same_username},
                                    context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def patient_identification_pm(request, patient_user_id):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor() or\
        logged_user_profile.is_administrative():
        next = request.GET.get('next', '')
        try:
            user = User.objects.get(id=patient_user_id)

            # CHECK IF DOCTOR CONTAINS THIS PATIENT
            if logged_user_profile.is_doctor():
                if not user in logged_user_profile.patients.all():
                    return HttpResponseRedirect(reverse('consulting_index'))

            return render_to_response(
                            'consulting/patient/patient_identification.html',
                            {'patient_user': user,
                            'patient_user_id': patient_user_id,
                            'next': next},
                            context_instance=RequestContext(request))
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))
    return HttpResponseRedirect(reverse('consulting_index'))


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
                                Q(role__exact=settings.PATIENT,
                                nif__istartswith=start)|
                                Q(role__exact=settings.PATIENT,
                                name__istartswith=start)|
                                Q(role__exact=settings.PATIENT,
                                first_surname__istartswith=start)|
                                Q(role__exact=settings.PATIENT,
                                second_surname__istartswith=start)).order_by(
                                'name', 'first_surname', 'second_surname')
            else:
                doctor_user = logged_user_profile.user
                profiles = Profile.objects.filter(
                                Q(doctor=doctor_user,
                                role__exact=settings.PATIENT,
                                nif__istartswith=start)|
                                Q(doctor=doctor_user,
                                role__exact=settings.PATIENT,
                                name__istartswith=start)|
                                Q(doctor=doctor_user,
                                role__exact=settings.PATIENT,
                                first_surname__istartswith=start)|
                                Q(doctor=doctor_user,
                                role__exact=settings.PATIENT,
                                second_surname__istartswith=start)).order_by(
                                'name', 'first_surname', 'second_surname')

            users =[]
            [users.append(profile.user) for profile in profiles]

            data = {'ok': True,
                    'completed_names':
                    [{'id': user.id,
                    'label':
                    (user.first_name + ' ' + user.last_name)}for user in users]
                    }
        return HttpResponse(simplejson.dumps(data))
    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def editpatient_pm(request, patient_user_id):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor() or\
        logged_user_profile.is_administrative():
        try:
            user = User.objects.get(id=patient_user_id)
            profile = user.get_profile()

            # CHECK IF DOCTOR CONTAINS THIS PATIENT
            if logged_user_profile.is_doctor():
                if not user in logged_user_profile.patients.all():
                    return HttpResponseRedirect(reverse('consulting_index'))

            if request.method == "POST":
                redirect_to = request.POST.get('next', '')
                if logged_user_profile.is_doctor():
                    exclude_list = ['user', 'role', 'doctor', 'patients',
                                    'username', 'illnesses']
                else:
                    exclude_list = ['user', 'role', 'doctor', 'patients',
                                    'username', 'illnesses', 'sex', 'status',
                                    'profession']

                request_params = dict([k, v] for k, v in request.POST.items())
                request_params.update({'created_by': request.user.id})

                form = ProfileForm(request_params, instance=profile,
                                    exclude_list=exclude_list)

                #Field to username
                name = profile.name
                first_surname = profile.first_surname
                nif = profile.nif
                dob = profile.dob

                if form.is_valid():
                    ######################## ACTIVE USER ######################
                    if format_string(form.cleaned_data['active']) == '1':
                        user.is_active = True
                    else:
                        user.is_active = False
                    user.save()
                    ###########################################################
                    profile = form.save(commit=False)
                    if not form.cleaned_data['postcode']:
                        profile.postcode = None

                    #Automatic to format name, first_surname and
                    #second_surname
                    profile.name = format_string(form.cleaned_data['name'])
                    profile.first_surname = format_string(
                                    form.cleaned_data['first_surname'])
                    profile.second_surname = format_string(
                                    form.cleaned_data['second_surname'])

                    #######################CHECK USERNAME #####################
                    #NUEVO USERNAME si se ha modificado el nombre o el
                    #primer apellido o el nif, o si ahora el nif está vacío y
                    #se ha modificado la fecha de nacimiento
                    name_form = form.cleaned_data['name']
                    first_surname_form = form.cleaned_data['first_surname']
                    nif_form = form.cleaned_data['nif']
                    dob_form = form.cleaned_data['dob']

                    if (name != name_form or\
                        first_surname != first_surname_form or\
                        nif != nif_form) or\
                        (nif_form == '' and dob != dob_form):
                        #NUEVO username
                        username = generate_username(form)
                        profile.user.username = username
                        profile.user.save()
                        profile.username = username

                        profile.save()

                        #SEN EMAIL to warn new username
                        sendemail(user)
                        patient_user_id = user.id

                        return HttpResponseRedirect(
                            '%s?next=%s' % (
                            reverse('consulting_patient_identification_pm',
                                    args=[patient_user_id]),
                            redirect_to))
                    else:
                        profile.save()
                        return HttpResponseRedirect(redirect_to)
                else:
                    return render_to_response(
                                    'consulting/patient/patient.html',
                                    {'form': form,
                                    'edit': True,
                                    'patient_user_id': patient_user_id,
                                    'next': redirect_to},
                                    context_instance=RequestContext(request))
            else:
                next = request.GET.get('next', '')
                if logged_user_profile.is_doctor():
                    exclude_list = ['user', 'role', 'doctor', 'patients',
                                    'username', 'illnesses']
                else:
                    exclude_list = ['user', 'role', 'doctor', 'patients',
                                    'username', 'illnesses', 'sex', 'status',
                                    'profession']

                if user.is_active:
                    active = settings.ACTIVE
                else:
                    active = settings.DEACTIVATE

                form = ProfileForm(instance=profile, exclude_list=exclude_list,
                                    initial={'active': active})

            return render_to_response('consulting/patient/patient.html',
                                    {'form': form,
                                    'edit': True,
                                    'patient_user_id': patient_user_id,
                                    'next': next},
                                    context_instance=RequestContext(request))
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


#METE EN SESIÓN EL PACIENTE
@login_required()
def pre_personal_data_pm(request, patient_user_id):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        try:
            User.objects.get(id=patient_user_id)
            request.session['patient_user_id'] = patient_user_id
            return HttpResponseRedirect(reverse('consulting_personal_data_pm'))
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def personal_data_pm(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        patient_user_id = request.session['patient_user_id']
        try:
            patient_user = User.objects.get(id=patient_user_id)

            # CHECK IF DOCTOR CONTAINS THIS PATIENT
            if logged_user_profile.is_doctor():
                if not patient_user in logged_user_profile.patients.all():
                    return HttpResponseRedirect(reverse('consulting_index'))

            return render_to_response(
                        'consulting/patient/personal_data_pm.html',
                        {'patient_user_id': patient_user.id,
                        'patient_user': patient_user},
                        context_instance=RequestContext(request))
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def patient_management(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        return render_to_response('consulting/pm/index_pm.html', {},
                            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


################################## MEDICINE ###################################
@login_required()
def searcher_component(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        data = {'ok': False}

        if request.method == 'POST':
            kind_component = request.POST.get("kind_component", "")
            start = request.POST.get("start", "").lower()

            if int(kind_component) == settings.ACTIVE_INGREDIENT:
                components = Component.objects.filter(
                Q(kind_component__exact=settings.ACTIVE_INGREDIENT),
                Q(name__istartswith=start) |
                Q(groups__name__istartswith=start)).distinct()
            else:
                #settings.MEDICINE
                components = Component.objects.filter(
                Q(kind_component__exact=settings.MEDICINE),
                Q(name__istartswith=start) |
                Q(groups__name__istartswith=start)).distinct()

            data = {'ok': True,
                    'components':
                        [{'id': c.id, 'label': (c.name)} for c in components]}
        return HttpResponse(simplejson.dumps(data))
    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def new_medicine_pm(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        patient_user_id = request.session['patient_user_id']
        patient_user = User.objects.get(id=patient_user_id)

        if request.method == "POST":
            request_params = dict([k, v] for k, v in request.POST.items())
            request_params.update({'created_by': request.user.id})
            form = MedicineForm(request_params)
            if form.is_valid():
                # COMPONENT CAN BE NEW OR ALREADY EXISTED
                component_name = form.cleaned_data['searcher_component']
                kind_component = form.cleaned_data['kind_component']
                try:
                    component = Component.objects.get(name=component_name,
                                kind_component=kind_component)
                except Component.DoesNotExist:
                    component_group = Group.objects.get(id=-1)
                    component = Component(name=component_name,
                                        kind_component=kind_component)
                    component.save()
                    component.groups.add(component_group)
                    component.save()
                medicine = form.save(commit=False)
                medicine.component = component
                medicine.patient = patient_user
                medicine.save()

                return HttpResponseRedirect(
                                        reverse('consulting_new_medicine_pm'))
        else:
            form = MedicineForm()

        return render_to_response(
                    'consulting/medicine/new_medicine_pm.html',
                    {'form': form,
                    'patient_user_id': patient_user_id,
                    'patient_user': patient_user},
                    context_instance=RequestContext(request))
    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@paginate(template_name='consulting/medicine/list_medicines_pm.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_medicines_before_pm(request):
    logged_user_profile = request.user.get_profile()

    patient_user_id = request.session['patient_user_id']

    if logged_user_profile.is_doctor():
        patient_user = User.objects.get(id=patient_user_id)

        medicines = Medicine.objects.filter(patient=patient_user,
        before_after_first_appointment=settings.BEFORE).order_by('-date')

        template_data = {}
        template_data.update({'patient_user': patient_user,
                                'medicines': medicines,
                                'patient_user_id': patient_user_id,
                                'csrf_token': get_token(request)})
        return template_data
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@paginate(template_name='consulting/medicine/list_medicines_pm.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_medicines_after_pm(request):
    logged_user_profile = request.user.get_profile()

    patient_user_id = request.session['patient_user_id']

    if logged_user_profile.is_doctor():
        patient_user = User.objects.get(id=patient_user_id)

        medicines = Medicine.objects.filter(patient=patient_user,
        before_after_first_appointment=settings.AFTER).order_by('-date')

        template_data = {}
        template_data.update({'patient_user': patient_user,
                                'medicines': medicines,
                                'patient_user_id': patient_user_id,
                                'csrf_token': get_token(request)})
        return template_data
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def detail_medicine_pm(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        if request.method == 'POST':
            medicine_id = request.POST.get("medicine_id", "")
            try:

                medicine = Medicine.objects.get(id=medicine_id)

                return render_to_response(
                                'consulting/medicine/detail_medicine.html',
                                {'medicine': medicine},
                                context_instance=RequestContext(request))
            except Medicine.DoesNotExist:
                    return HttpResponseRedirect(reverse('consulting_index'))

    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@paginate(template_name='consulting/medicine/list_medicines_ajax_pm.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def remove_medicine_pm(request):
    logged_user_profile = request.user.get_profile()
    if logged_user_profile.is_doctor():
        if request.method == 'POST':
            patient_user_id = request.session['patient_user_id']
            patient_user = User.objects.get(id=patient_user_id)
            medicine_id = request.POST.get("medicine_id", "")
            try:
                medicine = Medicine.objects.get(id=medicine_id)
                when = medicine.before_after_first_appointment
                medicine.delete()

                if when == settings.BEFORE:
                    medicines = Medicine.objects.filter(patient=patient_user,
                            before_after_first_appointment=settings.BEFORE)\
                            .order_by('-date')
                else:
                    medicines = Medicine.objects.filter(patient=patient_user,
                            before_after_first_appointment=settings.AFTER)\
                            .order_by('-date')

                template_data = {}
                template_data.update({'medicines': medicines})
                return template_data
            except Medicine.DoesNotExist:
                return HttpResponseRedirect(reverse('consulting_index'))
    return HttpResponseRedirect(reverse('consulting_index'))


###############################################################################
@login_required()
def administration(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        return render_to_response(
                    'consulting/administrative/index_administration.html', {},
                    context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


################################## STADISTICS #################################
@login_required()
def stratification(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        return render_to_response('consulting/patient/stratification.html', {},
                            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))
