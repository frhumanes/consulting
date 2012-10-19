# -*- encoding: utf-8 -*-
import time
import operator
from datetime import time as ttime
from datetime import date, timedelta, datetime

from random import randint

from decorators import paginate
from decorators import only_doctor_consulting, only_patient_consulting

from django.middleware.csrf import get_token
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.db.models import Q, Max
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import send_mail

from userprofile.models import Profile
from medicament.models import Component, Group
from consulting.models import Medicine, Task, Conclusion, Result, Answer
from cal.models import Appointment, Slot, SlotType
from illness.models import Illness
from survey.models import Survey, Block, Question, Option
from formula.models import Variable, Formula, Dimension
from private_messages.models import Message

from userprofile.forms import ProfileForm, ProfileSurveyForm
from consulting.forms import MedicineForm, TreatmentForm
from consulting.forms import  ConclusionForm
from consulting.forms import  ActionSelectionForm
from consulting.forms import SelectTaskForm
from consulting.forms import SelectOtherTaskForm
from consulting.forms import SelectNotAssessedVariablesForm
from consulting.forms import SymptomsWorseningForm, ParametersFilterForm
from illness.forms import IllnessSelectionForm, IllnessAddPatientForm
from survey.forms import SelectBlockForm
from survey.forms import QuestionsForm
from survey.forms import SelectBehaviorSurveyForm
from cal.forms import AppointmentForm

from cal.views import scheduler, day, app_add

from consulting.helper import strip_accents

from cal.utils import create_calendar
from cal.utils import mnames
from cal.utils import check_vacations
from cal.utils import get_doctor_preferences
from cal.utils import add_minutes

from wkhtmltopdf.views import *


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

        return render_to_response('consulting/patient/index_patient.html', {'patient_user':request.user.get_profile()},
                                context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


################################# CONSULTATION ################################
@login_required
@only_doctor_consulting
def select_year_month(request, id_patient, year, id_result=None):
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
                    patient=patient, patient_user=patient, id_result=id_result)
    if id_result:
        data.update({'id_result': id_result})

    return render_to_response("consulting/consultation/select_year_month.html",
                                data,
                                context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def today(request):
    y, m, d = time.localtime()[:3]

    return day(request, y, m, d)


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
def day_new_app(request, year, month, day, id_patient, id_result=None):
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
    if id_result:
        template_data.update({'id_result': id_result})

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

    return render_to_response("cal/includes/calendar.html",
        dict(year=year, month=month, user=request.user,
            month_days=lst, mname=mnames[month - 1]),
            context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def month_new_app(request, year, month, change, id_patient, id_result=None):
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

    template_data = dict(year=year, month=month, user=request.user,
                    month_days=lst, mname=mnames[month - 1], patient=patient)
    if id_result:
        template_data.update({'id_result': id_result})
    return render_to_response("consulting/consultation/month_new_app.html",
            template_data, context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def app_add(request, year, month, day, id_patient, id_result=None):
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
                appointment = form.save()

                if id_result:
                    result = get_object_or_404(Result, pk=int(id_result))
                    code = result.survey.code
                    if (code == settings.INITIAL_ASSESSMENT and\
                        result.task.completed) or\
                        (code == settings.ANXIETY_DEPRESSION_SURVEY):
                        return HttpResponseRedirect(
                            reverse('consulting_select_self_administered_survey',
                                        args=[appointment.id, id_result]))
                    else:
                        return HttpResponseRedirect(reverse('consulting_today'))
                else:
                    tasks = Task.objects.filter(
                                    survey__code=settings.INITIAL_ASSESSMENT,
                                    completed=True,
                                    patient=appointment.patient)
                    if tasks:
                        return HttpResponseRedirect(
                            reverse('consulting_select_self_administered_survey',
                                        args=[appointment.id]))
                    else:
                        return HttpResponseRedirect(reverse('consulting_today'))
            else:
                return render_to_response("consulting/consultation/new_app.html",
                    {'form': form,
                     'year': int(year), 'month': int(month), 'day': int(day),
                     'month_days': lst,
                     'mname': mname,
                     'doctor': doctor,
                     'patient': patient,
                     'id_result': id_result,
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
                 'id_result': id_result,
                 'doctor_preferences': doctor_preferences,
                 'free_intervals': free_intervals},
                context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def select_illness(request, id_appointment):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    if appointment.date < date.today():
        return HttpResponseRedirect(reverse('consulting_main',
                        kwargs={'id_appointment':id_appointment, 
                                'code_illness':0}))
    if request.method == 'POST':
        form = IllnessSelectionForm(request.POST,
                                    id_appointment=appointment.id)
        if form.is_valid():
            code_illness = form.cleaned_data['illness']
            if code_illness:
                return HttpResponseRedirect(reverse('consulting_main',
                        kwargs={'id_appointment':id_appointment, 
                                'code_illness': code_illness}))
            else:
                return HttpResponseRedirect(reverse('consulting_index'))
    else:
        form = IllnessSelectionForm(id_appointment=id_appointment)
    return render_to_response('consulting/consultation/illness/select.html',
                                {'form': form,
                                'patient_user': appointment.patient,
                                'id_appointment': id_appointment},
                                context_instance=RequestContext(request))



def check_task_completion(id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    answers = task.get_answers()
    if not answers:
        return False   
    if task.treated_blocks.count() < task.survey.num_blocks():
        return False
    questions = task.questions.filter(required=True)
    if not questions:
        questions = Question.objects.filter(required=True,kind__in=(0, task.patient.get_profile().sex), questions_categories__categories_blocks__kind__in=(settings.GENERAL, task.kind), questions_categories__categories_blocks__blocks_tasks=task)
    for question in questions:
        found = False
        for answer in answers:
            found = (answer.question == question)
            if found:
                break
        if not found:
            return False

    return True


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
                survey = get_object_or_404(Survey, code=settings.PREVIOUS_STUDY)

                tasks_with_survey = Task.objects.filter(
                                        patient=appointment.patient,
                                        survey=survey)
                if tasks_with_survey:
                    last_task_with_survey = tasks_with_survey.latest(
                                                            'creation_date')
                    if not last_task_with_survey.is_completed():
                        return HttpResponseRedirect(
                                reverse('consulting_administrative_data',
                                        args=[last_task_with_survey.id,
                                                id_appointment]))
                task = Task(created_by=request.user,
                    patient=appointment.patient, survey=survey,
                    appointment=appointment, self_administered=False)
                task.save()
                return HttpResponseRedirect(
                                reverse('consulting_administrative_data',
                                        args=[task.id, id_appointment]))
    else:
        form = ActionSelectionForm()
    return render_to_response('consulting/consultation/action/select.html',
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
                conclusion.task = result.task
                conclusion.save()

                if result.survey.code == settings.PREVIOUS_STUDY:
                    return HttpResponseRedirect(
                        reverse('consulting_add_illness', args=[conclusion.id]))

            return HttpResponseRedirect(
                                reverse('consulting_new_medicine_conclusion',
                                        args=[conclusion.id]))
    else:
        conclusion = Conclusion(observation=request)
        form = ConclusionForm()

    return render_to_response('consulting/consultation/conclusion/conclusion.html',
                                {'form': form,
                                'patient_user': appointment.patient,
                                'id_appointment': id_appointment,
                                'id_result': id_result},
                                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def add_illness(request, id_conclusion):
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
                                    reverse('consulting_add_illness',
                                    args=[id_conclusion]))
    else:
        form = IllnessAddPatientForm(instance=patient.get_profile())

    return render_to_response(
                        'consulting/consultation/add_illness.html',
                        {'form': form,
                        'conclusion': conclusion,
                        'patient_user': patient,
                        'year': time.localtime()[0]},
                        context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def select_self_administered_survey(request, id_appointment, id_result=None):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    if id_result:
        tmp_result = get_object_or_404(Result, pk=int(id_result))
        if tmp_result.task.is_completed():
            result = tmp_result
        else:
            results = Result.objects.filter(patient=appointment.patient,
                                            task__completed=True)
            if results:
                result = results.latest('date')
            else:
                return HttpResponseRedirect(reverse('consulting_index'))
    else:
        results = Result.objects.filter(patient=appointment.patient,
                                        task__completed=True)
        if results:
            result = results.latest('date')
        else:
            return HttpResponseRedirect(reverse('consulting_index'))

    code = result.survey.code
    if not (code == settings.INITIAL_ASSESSMENT or\
            code == settings.ANXIETY_DEPRESSION_SURVEY):
        return HttpResponseRedirect(reverse('consulting_index'))

    variables = get_variables(result.id, settings.DEFAULT_NUM_VARIABLES)

    if request.method == 'POST':
        form = SelectTaskForm(request.POST, variables=variables)
        if form.is_valid():
            code_survey = form.cleaned_data['survey']
            previous_days = form.cleaned_data['previous_days']
            kind = form.cleaned_data['kind']

            if code_survey == str(settings.ANXIETY_DEPRESSION_SURVEY) and kind == settings.EXTENSO:
                survey = get_object_or_404(Survey,
                                code=settings.ANXIETY_DEPRESSION_SURVEY)
                exc_block = get_object_or_404(Block,
                                code=settings.BEHAVIOR_BLOCK, kind=settings.EXTENSO)
            else:
                exc_block = get_object_or_404(Block,
                                code=settings.BEHAVIOR_BLOCK, kind=settings.ABREVIADO)
                survey = get_object_or_404(Survey,
                                code=settings.ANXIETY_DEPRESSION_SURVEY)

            task = Task(created_by=request.user, patient=appointment.patient,
            appointment=appointment, self_administered=True, survey=survey,
            previous_days=previous_days, kind=kind)
            task.save()

            id_variables = form.cleaned_data['variables']
            if id_variables and code_survey==str(settings.CUSTOM):
                variables = Variable.objects.filter(id__in=id_variables)
                for variable in variables:
                    formulas = variable.variable_formulas.filter(kind=kind)
                    for formula in formulas:
                        codes = formula.polynomial.split('+')
                        for code in codes:
                            try:
                                question = Question.objects.exclude(questions_categories__categories_blocks=exc_block).get(code=code)
                                task.questions.add(question)
                            except:
                                pass
            elif code_survey==str(settings.CUSTOM):
                form = SelectTaskForm(variables=variables)
                return render_to_response('consulting/consultation/monitoring/finish/select_self_administered_survey.html',
                                            {'form': form,
                                            'appointment': appointment,
                                            'code_variables': settings.CUSTOM,
                                            'patient_user': appointment.patient,
                                            'appointment': appointment},
                                            context_instance=RequestContext(request))
            else:## HIDE DOCTOR's QUESTIONS
                questions_list = Question.objects.filter(questions_categories__categories_blocks__blocks_surveys=survey).exclude(questions_categories__categories_blocks=exc_block)
                for question in questions_list:
                    task.questions.add(question)

            return HttpResponseRedirect(reverse('consulting_index'))
    else:
        form = SelectTaskForm(variables=variables)

    return render_to_response(
                'consulting/consultation/select_self_administered_survey.html',
                {'form': form,
                'id_appointment': id_appointment,
                'id_result': result.id,
                'code_variables': settings.CUSTOM,
                'patient_user': appointment.patient},
                context_instance=RequestContext(request))





def new_result_sex_status(id_logged_user, id_task, id_appointment):
    logged_user = get_object_or_404(User, pk=int(id_logged_user))
    task = get_object_or_404(Task, pk=int(id_task))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    profile = task.patient.get_profile()
    my_block = get_object_or_404(Block, code=int(settings.ADMINISTRATIVE_DATA))

    #try:
    #    result = Result.objects.get(patient=task.patient, 
    #                                survey=task.survey, task=task,
    #                                created_by=logged_user, 
    #                                appointment=appointment)
    #except:
    #NEW RESULT
    result = Result(patient=task.patient, 
                    survey=task.survey, 
                    task=task,
                    block=my_block,
                    created_by=logged_user, 
                    appointment=appointment)
    result.save()

    if task.task_results.count() == 1:
        task.start_date = result.date
        task.save()

    #SEX
    if profile.sex == settings.WOMAN:
        sex_option = get_object_or_404(Option, code=settings.CODE_WOMAN)
    else:
        sex_option = get_object_or_404(Option, code=settings.CODE_MAN)

    #STATUS
    status = profile.status
    if status == settings.MARRIED:
        status_option = get_object_or_404(Option, code=settings.CODE_MARRIED)
    elif status == settings.STABLE_PARTNER:
        status_option = get_object_or_404(Option, code=settings.CODE_STABLE_PARTNER)
    elif status == settings.DIVORCED:
        status_option = get_object_or_404(Option, code=settings.CODE_DIVORCED)
    elif status == settings.WIDOW_ER:
        status_option = get_object_or_404(Option, code=settings.CODE_WIDOW_ER)
    elif status == settings.SINGLE:
        status_option = get_object_or_404(Option, code=settings.CODE_SINGLE)
    elif status == settings.OTHER:
        status_option = get_object_or_404(Option, code=settings.CODE_OTHER)

    #UPDATE RESULT
    answer = Answer(result = result, option = sex_option)
    answer.save()
    answer = Answer(result = result, option = status_option)
    answer.save()
    result.save()

    return result


@login_required()
@only_doctor_consulting
def administrative_data(request, id_task, code_block=None, code_illness=None, id_appointment=None):
    task = get_object_or_404(Task, pk=int(id_task))
    user = task.patient
    profile = user.get_profile()
    block = get_object_or_404(Block, code=int(code_block))

    treated_blocks = task.treated_blocks.all()

    # CHECK IF DOCTOR CONTAINS THIS PATIENT
    if not user in request.user.get_profile().patients.all():
        return HttpResponseRedirect(reverse('consulting_index'))

    if request.method == "POST":
        exclude_list = ['user', 'role', 'doctor', 'patients', 'username',
                        'illnesses']

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
                result = new_result_sex_status(request.user.id, task.id,
                                                id_appointment)

                if block not in treated_blocks:
                    task.treated_blocks.add(block)

                if check_task_completion(task.id):
                    task.completed = True
                    task.end_date = datetime.now()
                    task.save()

                #SEN EMAIL to warn new username
                sendemail(user)

                return render_to_response(
                                    'consulting/consultation/warning.html',
                                    {'patient_user': user,
                                    'id_result': result.id,
                                    'code_block': code_block},
                                    context_instance=RequestContext(request))
            else:
                profile.save()
                result = new_result_sex_status(request.user.id, task.id,
                                                id_appointment)

                if block not in treated_blocks:
                    task.treated_blocks.add(block)

                if check_task_completion(task.id):
                    task.completed = True
                    task.end_date = datetime.now()
                    task.save()

                return next_block(task, block, code_illness, id_appointment)
        else:
            return render_to_response(
                            'consulting/consultation/administrative_data.html',
                            {'form': form,
                            'patient_user': user,
                            'task': task,
                            'id_appointment': id_appointment,
                            'my_block': block},
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
                            'task': task,
                            'id_appointment': id_appointment,
                            'my_block': block},
                            context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def show_block(request, id_task, code_block=None, code_illness=None, id_appointment=None):
    task = get_object_or_404(Task, pk=int(id_task))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    if code_block is None or code_block == str(0):
        block = task.survey.blocks.filter(kind__in=(settings.GENERAL,task.kind)).order_by('code')[0]
        return HttpResponseRedirect(
                            reverse('consulting_show_task_block',
                                    kwargs={'id_task':task.id,
                                            'code_block':block.code, 
                                            'code_illness':code_illness, 
                                            'id_appointment':id_appointment
                                            }))
    elif code_block == str(settings.ADMINISTRATIVE_DATA):
        return administrative_data(request, id_task=id_task, code_block=code_block, code_illness=code_illness, id_appointment=id_appointment)
    else:
        block = get_object_or_404(Block, code=int(code_block), kind__in=(settings.GENERAL, task.kind))
    treated_blocks = task.treated_blocks.all()
    dic = {}
    questions = task.questions.all()
    if not questions or int(code_block) != settings.ANXIETY_DEPRESSION_BLOCK:
        categories = block.categories.all().order_by('id')
        for category in categories:
            questions = category.questions.filter(kind__in=[settings.UNISEX, task.patient.get_profile().sex]).order_by('id')
            for question in questions:
                options = question.question_options.all().order_by('id')
                dic[question.id] = [(option.id, option.text)for option in options]
    else:
        for question in questions:
            options = question.question_options.all().order_by('id')
            dic[question.id] = [(option.id, option.text)for option in options]
    if request.method == 'POST':
        form = QuestionsForm(request.POST, dic=dic, selected_options=[])
        if form.is_valid():
            new_result = Result(patient=task.patient, 
                            survey=task.survey, 
                            task=task,
                            block=block,
                            created_by=task.created_by, 
                            appointment=task.appointment)
            new_result.save()
            items = {}
            answers = {}
            for name_field, values in form.cleaned_data.items():
                if name_field.endswith('_value'):
                    answers[name_field[:name_field.find('_value')]] = values
                else:
                    items[name_field] = values

            for name_field, values in items.items():
                if name_field in answers.keys():
                    value = answers[name_field]
                else:
                    value = None
                if isinstance(values, list):
                    for value in values:
                        option = Option.objects.get(pk=int(value))
                        answer = Answer(result = new_result, option = option, value = value)
                        answer.save()
                elif values:
                    option = Option.objects.get(pk=int(values))
                    answer = Answer(result = new_result, option = option, value = value)
                    answer.save()


            if block not in treated_blocks:
                task.treated_blocks.add(block)
            if not task.start_date:
                task.start_date = datetime.now()
            task.updated_at = datetime.now()
            if check_task_completion(task.id):
                task.completed = True
                task.appointment = appointment
                task.end_date = datetime.now()
            task.save()

            return next_block(task, block, code_illness, id_appointment)
    else:
        last_result = None
        try: 
            last_result =  task.task_results.filter(block=block).latest('date')
            selected_options = last_result.options.all()
        except:
            if code_block == str(settings.PRECEDENT_RISK_FACTOR):
                try:
                    last_result =  Result.objects.filter(block=block,patient=task.patient).latest('date')
                    selected_options = last_result.options.all()
                except:
                    selected_options = []
            else:
                selected_options = []
        form = QuestionsForm(dic=dic, selected_options=selected_options)

    return render_to_response('consulting/consultation/block.html',
                            {'form': form,
                            'task':task,
                            'result': last_result,
                            'appointment': appointment,
                            'my_block': block,
                            'patient_user': task.patient},
                            context_instance=RequestContext(request))


def next_block(task, block, code_illness, id_appointment):
    available_blocks = task.survey.blocks.filter(code__gt=block.code,kind__in=(settings.GENERAL, task.kind)).order_by('code')
    if available_blocks:
        return HttpResponseRedirect(
                            reverse('consulting_show_task_block',
                                    kwargs={'id_task':task.id,
                                            'code_block':available_blocks[0].code, 
                                            'code_illness':code_illness, 
                                            'id_appointment':id_appointment
                                            }))
    elif task.self_administered and not block.code == settings.BEHAVIOR_BLOCK:
        return HttpResponseRedirect(
                            reverse('consulting_show_task_block',
                                    kwargs={'id_task':task.id,
                                            'code_block':settings.BEHAVIOR_BLOCK, 
                                            'code_illness':code_illness, 
                                            'id_appointment':id_appointment
                                            }))
    elif task.completed:
        return HttpResponseRedirect(
                            reverse('consulting_finished_task',
                                    kwargs={'id_task':task.id,
                                            'code_illness':code_illness, 
                                            'id_appointment':id_appointment
                                            }))
    else:
        return HttpResponseRedirect(
                            reverse('consulting_main',
                                    kwargs={'code_illness':code_illness, 
                                            'id_appointment':id_appointment
                                            }))

@login_required()
@only_patient_consulting
def self_administered_block(request, id_task):
    task = get_object_or_404(Task, pk=int(id_task))

    if task.task_results.all():
        last_result = task.task_results.latest('date')

        if last_result:
            selected_options = last_result.options.all()
    else:
        selected_options = []

    dic = {}
    treated_blocks = task.treated_blocks.all()
    block = task.survey.blocks.all()[0]
    questions = task.questions.all()
    if questions:
        for question in questions:
            options = question.question_options.all().order_by('id')
            dic[question.id] = [
                            (option.id, option.text)for option in options]
    else:
        categories = block.categories.all().order_by('id')

        for category in categories:
            questions = category.questions.all().order_by('id')
            for question in questions:
                options = question.question_options.all().order_by('id')
                dic[question.id] = [
                                (option.id, option.text)for option in options]

    if request.method == 'POST':
        form = QuestionsForm(request.POST, dic=dic,
                                        selected_options=selected_options)

        if form.is_valid():
            result = Result(patient=task.patient, survey=task.survey, task=task,block=block,
                    created_by=request.user)
            result.save()

            if task.task_results.count() == 1:
                task.start_date = result.date
                task.save()

            items = form.cleaned_data.items()
            for name_field, values in items:
                if isinstance(values, list):
                    for value in values:
                        option = Option.objects.get(pk=int(value))
                        answer = Answer(result = result, option = option)
                        answer.save()
                elif values:
                    option = Option.objects.get(pk=int(values))
                    answer = Answer(result = result, option = option)
                    answer.save()

            if block not in treated_blocks:
                task.treated_blocks.add(block)

            if check_task_completion(task.id):
                task.completed = True
                task.end_date = datetime.now()
                task.save()

            return HttpResponseRedirect(
                    reverse('consulting_symptoms_worsening', args=[task.id]))
    else:
        form = QuestionsForm(dic=dic, selected_options=selected_options)

    return render_to_response('consulting/patient/surveys/block.html',
                            {'form': form,
                            'task': task},
                            context_instance=RequestContext(request))


@login_required()
@only_patient_consulting
def symptoms_worsening(request, id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    if request.method == 'POST':
        form = SymptomsWorseningForm(request.POST)
        answer = int(request.POST.get("question", 0))
        if form.is_valid() and answer:
            symptoms_worsening = form.cleaned_data['symptoms_worsening']
            task.observations = symptoms_worsening
            task.save()
            return HttpResponseRedirect(reverse('consulting_list_surveys'))
        elif not answer:
            return HttpResponseRedirect(reverse('consulting_list_surveys'))
    else:
        form = SymptomsWorseningForm()
    return render_to_response('consulting/patient/surveys/symptoms_worsening.html',
                                {'form': form,
                                'id_task': task.id},
                                context_instance=RequestContext(request))


################################## MONITORING #################################
@login_required()
@only_doctor_consulting
def monitoring(request, id_appointment, code_illness=None):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    temp = []
    previous = {}
    tasks = Task.objects.filter(appointment=appointment)
    if not code_illness or appointment.date < date.today():
        illness = None
    else:
        illness = get_object_or_404(Illness, code=int(code_illness))
        if not tasks.count():
            tasks = []
            latest_tasks = Task.objects.filter(patient=appointment.patient, completed=True, survey__surveys_illnesses__code=code_illness).order_by('-end_date')
            for task in latest_tasks:
                variables = task.get_variables_mark()
                temp.append(variables)
                tasks.insert(0, task)
                if len(temp) == 2:
                    for v in variables.keys():
                        previous[v] = (temp[1][v], temp[0][v])
                    break
                else:
                    for v in variables.keys():
                        previous[v] = (temp[0][v],)
    medicaments_list = Medicine.objects.filter(appointment=appointment, date__isnull=True, is_previous=False)
    conclusions = Conclusion.objects.filter(appointment=appointment)
    return render_to_response(
                'consulting/consultation/monitoring/index.html',
                {'patient_user': appointment.patient,
                'appointment': appointment,
                'illness': illness,
                'treatment': medicaments_list,
                'conclusions': conclusions,
                'previous_marks': previous,
                'tasks': tasks},
                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
@paginate(
    template_name='consulting/consultation/monitoring/incomplete_surveys/list.html',
    list_name='tasks', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_incomplete_tasks(request, id_appointment, code_illness, self_administered=False):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    illness = get_object_or_404(Illness, code=int(code_illness))
    patient = appointment.patient
    tasks = Task.objects.filter(
    Q(patient=patient, completed=False, self_administered=self_administered,
        assess=True,survey__surveys_illnesses__code=code_illness)).order_by('-creation_date')

    template_data = {}
    template_data.update({'patient_user': patient,
                        'tasks': tasks,
                        'appointment': appointment,
                        'illness':illness,
                        'csrf_token': get_token(request)})
    return template_data


@login_required()
@only_doctor_consulting
def not_assess_task(request, id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    task.assess = False
    task.end_date = datetime.now()
    task.save()

    return HttpResponse('Tarea marcada correctamente')


@login_required()
@only_doctor_consulting
def resume_task(request, id_appointment, code_illness, id_task):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    task = get_object_or_404(Task, pk=int(id_task))
    if int(code_illness):
        illness = get_object_or_404(Illness, pk=int(code_illness))
    else:
        illness = Illness.objects.none()
    if task.survey.code == settings.ANXIETY_DEPRESSION_SURVEY or task.survey.code == settings.INITIAL_ASSESSMENT:
        variables = task.get_variables_mark()
        dimensions = task.get_dimensions_mark(variables)
        return render_to_response(
        'consulting/consultation/monitoring/incomplete_surveys/variables_mark.html',
                {'variables': variables,
                 'dimensions': dimensions,
                 'task': task,
                'appointment': appointment,
                'illness': illness,
                'patient_user': appointment.patient},
                context_instance=RequestContext(request))
    elif task.survey.code == settings.ADHERENCE_TREATMENT:
        tasks = Task.objects.filter(patient=task.patient,survey__code=settings.ADHERENCE_TREATMENT, completed=True).order_by('end_date')
        values = {}
        
        mindate = tasks.latest('end_date').end_date
        maxdate = tasks.latest('end_date').end_date
        for t in tasks:
            mindate = t.end_date < mindate and t.end_date or mindate
            maxdate = t.end_date > maxdate and t.end_date or maxdate
            for a in t.get_answers():
                if a.question.code in values:
                    values[a.question.code].append((t.end_date, a.weight))
                else:
                    values[a.question.code] =[(t.end_date, a.weight),]
        ticks = (mindate, maxdate)
        return render_to_response(
        'consulting/consultation/monitoring/treatment_survey/evolution.html',
                {'values': values,
                 'task': task,
                 'ticks': ticks,
                'appointment': appointment,
                'illness': illness,
                'patient_user': appointment.patient},
                context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_main',kwargs={'code_illness':code_illness,'id_appointment':id_appointment}))


def get_not_assessed_variables(id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    lq = [q.code for q in task.questions.all()]
    not_assessed_variables = []
    if lq:
        for f in Formula.objects.filter(kind=task.kind).exclude(reduce(operator.or_, (Q(polynomial__contains=x) for x in lq))).distinct():
            not_assessed_variables.append((f.variable.id, f.variable.name))
    return not_assessed_variables


@login_required()
@only_doctor_consulting
def config_task_variables(request, id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    variables = get_not_assessed_variables(task.id)

    if request.method == 'POST':
        form = SelectNotAssessedVariablesForm(request.POST, variables=variables)
        if form.is_valid():
            kind = task.kind

            id_variables = form.cleaned_data['variables']

            variables = Variable.objects.filter(id__in=id_variables)
            for variable in variables:
                formulas = variable.variable_formulas.filter(kind=task.kind)
                for formula in formulas:
                    codes = formula.polynomial.split('+')
                    for code in codes:
                        question = get_object_or_404(Question, code=code)
                        if question not in task.questions.all():
                            task.questions.add(question)

            return HttpResponseRedirect('')
    else:
        form = SelectNotAssessedVariablesForm(variables=variables)

    return render_to_response(
                'consulting/consultation/monitoring/complete_self_administered_survey/select_not_assessed_variables.html',
                {'form': form,
                'patient_user': task.patient},
                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def select_successive_survey(request, id_appointment, code_illness=None):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    illness = get_object_or_404(Illness, code=int(code_illness))
    variables = {}
    tasks = Task.objects.filter(
    Q(patient=appointment.patient, completed=True,
        survey__surveys_illnesses__code=code_illness))
    if tasks.count() > 0:
        latest_task = tasks.latest('end_date')
        variables = latest_task.get_list_variables(settings.DEFAULT_NUM_VARIABLES)

    if code_illness == str(settings.DEFAULT_ILLNESS):
        ClassForm = ActionSelectionForm
    elif code_illness == str(settings.ANXIETY_DEPRESSION):
        ClassForm = SelectOtherTaskForm

    if request.method == 'POST':
        form = ClassForm(request.POST, variables=variables)
        if form.is_valid():
            code_survey = form.cleaned_data['survey']
            if 'kind' in form.cleaned_data:
                kind = form.cleaned_data['kind']
            else:
                kind = settings.GENERAL
           
            if code_survey == str(settings.CUSTOM):
                survey = get_object_or_404(Survey, code=int(settings.ANXIETY_DEPRESSION_SURVEY))
            else:
                survey = get_object_or_404(Survey, code=int(code_survey))

            task = Task(created_by=request.user, patient=appointment.patient,
            appointment=appointment, self_administered=False, survey=survey, kind=kind)
            task.save()

            if 'variables' in form.cleaned_data:
                id_variables = form.cleaned_data['variables']
                if id_variables and code_survey == str(settings.CUSTOM):
                    variables = Variable.objects.filter(id__in=id_variables)
                    for variable in variables:
                        formulas = variable.variable_formulas.filter(kind=kind)
                        for formula in formulas:
                            codes = formula.polynomial.split('+')
                            for code in codes:
                                question = Question.objects.get(code=code)
                                task.questions.add(question)

            return HttpResponseRedirect(reverse('consulting_show_task_block',
                                kwargs={'id_task':task.id, 
                                        'id_appointment':id_appointment,
                                        'code_illness':code_illness,
                                        'code_block':0
                                        }))
    else:
        form = ClassForm(variables=variables)

    return render_to_response(
            'consulting/consultation/monitoring/successive_survey/select.html',
            {'form': form,
            'appointment': appointment,
            'illness': illness,
            'code_variables': settings.CUSTOM,
            'patient_user': appointment.patient},
            context_instance=RequestContext(request))



@login_required()
@only_doctor_consulting
def prev_treatment_block(request, id_appointment, code_illness=None):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))

    survey = Survey.objects.get(code=settings.ADHERENCE_TREATMENT)
    try:
        task = Task.objects.get(appointment=appointment, survey=survey)
    except:
        task = Task(appointment=appointment, survey=survey,created_by=request.user,self_administered=False, patient=appointment.patient)
        task.save()

    return HttpResponseRedirect(reverse('consulting_show_task_block',
                    kwargs={'id_task':task.id,
                            'code_block':0, 
                            'code_illness':code_illness, 
                            'id_appointment':id_appointment
                            }))


@login_required()
@only_doctor_consulting
def treatment_block(request, id_task, id_appointment):
    task = get_object_or_404(Task, pk=int(id_task))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))

    at_survey = get_object_or_404(Survey, code=settings.ADHERENCE_TREATMENT)

    dic = {}
    treated_blocks = task.treated_blocks.all()
    block = at_survey.blocks.all()[0]
    categories = block.categories.all().order_by('id')

    for category in categories:
        questions = category.questions.all().order_by('id')
        for question in questions:
            options = question.question_options.all().order_by('id')
            dic[question.id] = [
                            (option.id, option.text)for option in options]

    if request.method == 'POST':
        form = QuestionsForm(request.POST, dic=dic, selected_options=[])

        if form.is_valid():
            result = Result(patient=task.patient, survey=at_survey, task=task,
                    created_by=request.user, appointment=appointment, block=block)
            result.save()

            task.start_date = result.date
            task.save()

            items = form.cleaned_data.items()
            for name_field, values_list in items:
                if values_list:
                    if isinstance(values_list, list):
                        for value in values_list:
                            option = Option.objects.get(pk=int(value))
                            answer = Answer(result = result, option = option)
                            answer.save()
                    elif values_list:
                        option = Option.objects.get(pk=int(values_list))
                        answer = Answer(result = result, option = option)
                        answer.save()

            if block not in treated_blocks:
                task.treated_blocks.add(block)

            if check_task_completion(task.id):
                task.completed = True
                task.end_date = datetime.now()
                task.save()

            return HttpResponseRedirect(reverse('consulting_monitoring',
                                                args=[id_appointment]))

    else:
        form = QuestionsForm(dic=dic, selected_options=[])

    return render_to_response(
    'consulting/consultation/monitoring/treatment_survey/block.html',
    {'form': form,
    'task': task,
    'appointment': appointment,
    'my_block': block,
    'patient_user': task.patient},
    context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def conclusion_monitoring(request, id_appointment, code_illness):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    illness= get_object_or_404(Illness, code=int(code_illness))

    if request.method == 'POST':
        request_params = dict([k, v] for k, v in request.POST.items())
        request_params.update({'created_by': request.user.id})
        form = ConclusionForm(request_params)
        if form.is_valid():
            conclusion = form.save(commit=False)
            conclusion.patient = appointment.patient
            conclusion.appointment = appointment
            conclusion.save()

            return HttpResponseRedirect(
                                reverse('consulting_main',
                                        kwargs={'id_appointment':id_appointment,'code_illness':code_illness}))
    else:
        conclusion = None#Conclusion.objects.get(appointment=appointment)
        if not conclusion and 'notes' in request.session:
            conclusion = Conclusion(observation=request.session["notes"])
        form = ConclusionForm(instance=conclusion)

    return render_to_response(
                'consulting/consultation/monitoring/finish/conclusion.html',
                {'form': form,
                'patient_user': appointment.patient,
                'appointment': appointment,
                'illness':illness},
                context_instance=RequestContext(request))

@login_required
@only_doctor_consulting
def new_app(request, id_appointment, code_illness):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    illness= get_object_or_404(Illness, code=int(code_illness))
    request.session['appointment'] = appointment
    request.session['illness'] = illness
    patient_user = appointment.patient
    return scheduler(request, patient_user.id)


@login_required()
@only_doctor_consulting
def select_self_administered_survey_monitoring(request, id_appointment, code_illness):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    illness = get_object_or_404(Illness, code=int(code_illness))
    task = Task.objects.filter(
            Q(patient=appointment.patient,
            survey__surveys_illnesses__code=code_illness))

    if task.count() > 0:
        task = task.latest('end_date')
        variables = task.get_list_variables(settings.DEFAULT_NUM_VARIABLES)
    else:
        variables = []


    if request.method == 'POST':
        form = SelectTaskForm(request.POST, variables=variables)
        if form.is_valid():
            code_survey = form.cleaned_data['survey']
            previous_days = form.cleaned_data['previous_days']
            kind = form.cleaned_data['kind']
            if code_survey == str(settings.CUSTOM):
                survey = get_object_or_404(Survey,
                                code=settings.ANXIETY_DEPRESSION_SURVEY)
            else:
                survey = get_object_or_404(Survey,
                                code=code_survey)
            exc_block = get_object_or_404(Block,code=settings.BEHAVIOR_BLOCK, kind=kind)

            task = Task(created_by=request.user, patient=appointment.patient,
            appointment=None, self_administered=True, survey=survey,
            previous_days=previous_days, kind=kind)
            task.save()


            id_variables = form.cleaned_data['variables']
            if id_variables and code_survey==str(settings.CUSTOM):
                variables = Variable.objects.filter(id__in=id_variables)
                for variable in variables:
                    formulas = variable.variable_formulas.filter(formula__kind=kind)
                    for formula in formulas:
                        codes = formula.polynomial.split('+')
                        for code in codes:
                            try:
                                question = Question.objects.exclude(questions_categories__categories_blocks=exc_block).get(code=code)
                                task.questions.add(question)
                            except:
                                pass
            elif code_survey==str(settings.CUSTOM):
                form = SelectTaskForm(variables=variables)
                return render_to_response('consulting/consultation/monitoring/finish/select_self_administered_survey.html',
                                            {'form': form,
                                            'appointment': appointment,
                                            'code_variables': settings.CUSTOM,
                                            'patient_user': appointment.patient,
                                            'appointment': appointment},
                                            context_instance=RequestContext(request))
            else:## HIDE DOCTOR's QUESTIONS
                questions_list = Question.objects.filter(questions_categories__categories_blocks__blocks_surveys=survey, questions_categories__categories_blocks__kind=kind).exclude(questions_categories__categories_blocks=exc_block)
                for question in questions_list:
                    task.questions.add(question)


            return HttpResponseRedirect(reverse('consulting_main',
                                        kwargs={'code_illness':code_illness,
                                                'id_appointment':id_appointment
                                               }))
            
    else:
        form = SelectTaskForm(variables=variables)

    return render_to_response(
            'consulting/consultation/monitoring/finish/select_self_administered_survey.html',
            {'form': form,
            'appointment': appointment,
            'code_variables': settings.CUSTOM,
            'patient_user': appointment.patient,
            'illness': illness},
            context_instance=RequestContext(request))


########################### PATIENT ###################################
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
    subject = render_to_string('registration/identification_email_subject.txt',
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
                    user.get_profile().get_full_name()}for user in users]
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


@login_required()
@paginate(template_name='consulting/patient/surveys/list.html',
    list_name='tasks', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_surveys(request):
    tasks = request.user.get_profile().get_pending_tasks()
    template_data = {}
    template_data.update({'tasks': tasks})
    return template_data


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
                        [{'id': c.id, 'label': (c.name)} for c in components.order_by('name')]}
        return HttpResponse(simplejson.dumps(data))
    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def add_medicine(request, action, id_appointment=None):
    logged_user_profile = request.user.get_profile()
    if action == 'register':
        ClassForm = MedicineForm
        filter_option = 'previous'
    elif action == 'prescribe':
        ClassForm = TreatmentForm
        filter_option = 'current'
    elif action == 'remove':
        return remove_medicine(request)
    elif action == 'stop':
        return stop_medicine(request)
    if logged_user_profile.is_doctor():
        if id_appointment:
            appointment = get_object_or_404(Appointment,pk=int(id_appointment))
            patient_user = appointment.patient
        else:
            patient_user_id = request.session['patient_user_id']
            patient_user = User.objects.get(id=patient_user_id)

        if request.method == "POST":
            request_params = dict([k, v] for k, v in request.POST.items())
            request_params.update({'created_by': request.user.id})
            form = ClassForm(request_params)
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
                if action == 'register':
                    medicine.is_previous = True
                if id_appointment:
                    medicine.appointment = appointment
                medicine.component = component
                medicine.patient = patient_user
                medicine.save()

                return HttpResponseRedirect(reverse('consulting_get_medicines', kwargs={'filter_option':filter_option, 'id_patient':patient_user.id}))
        else:
            form = ClassForm()

        return render_to_response(
                    'consulting/medicine/medicine.html',
                    {'form': form,
                    'patient_user': patient_user},
                    context_instance=RequestContext(request))
    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@only_doctor_consulting
@paginate(template_name='consulting/patient/list_medicines.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def get_medicines(request, filter_option, id_patient):
    logged_user_profile = request.user.get_profile()

    if id_patient:
        patient_user = User.objects.get(pk=int(id_patient))
    else:
        patient_user_id = request.session['patient_user_id']
        patient_user = User.objects.get(id=patient_user_id)
        appointment = None
        illness = None
    if filter_option == 'old':
        template_name = 'consulting/medicine/list_old_treatment.html'
        medicines = Medicine.objects.filter(is_previous=False, date__isnull=False, patient=patient_user)
    elif filter_option == 'previous':
        template_name = 'consulting/medicine/list_previous_treatment.html'
        medicines = Medicine.objects.filter(is_previous=True, patient=patient_user)
    elif filter_option == 'current':
        template_name = 'consulting/medicine/list_current_treatment.html'
        medicines = Medicine.objects.filter(is_previous=False, date__isnull=True, patient=patient_user)
    else:
        medicines = patient.get_profile().get_treatment()

    template_data = {}
    template_data.update({'patient_user': patient_user,
                            'medicines': medicines.order_by('-created_at'),
                            'patient_user': patient_user,
                            'filter_option': filter_option,
                            'template_name': template_name,
                            'csrf_token': get_token(request)})
    return template_data

@login_required()
@only_doctor_consulting
def list_medicines(request, id_appointment=None, code_illness=None):
    logged_user_profile = request.user.get_profile()

    if id_appointment and code_illness:
        appointment = Appointment.objects.get(pk=int(id_appointment))
        patient_user = appointment.patient
        illness = Illness.objects.get(code=int(code_illness))
    else:
        patient_user_id = request.session['patient_user_id']
        patient_user = User.objects.get(id=patient_user_id)
        appointment = None
        illness = None


    return render_to_response('consulting/patient/list_medicines.html', 
                            {'patient_user': patient_user,
                            'appointment':appointment,
                            'illness': illness,
                            },
                    context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
@paginate(template_name='consulting/patient/list_appointments.html',
    list_name='events', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_appointments(request):
    logged_user_profile = request.user.get_profile()

    patient_user_id = request.session['patient_user_id']

    patient_user = User.objects.get(id=patient_user_id)

    appointments = Appointment.objects.filter(patient=patient_user).order_by('-date')

    template_data = {}
    template_data.update({'patient_user': patient_user,
                            'events': appointments,
                            'patient_user_id': patient_user_id,
                            'csrf_token': get_token(request)})
    return template_data


@login_required()
def remove_medicine(request):
    logged_user_profile = request.user.get_profile()
    if logged_user_profile.is_doctor():
        if request.method == 'POST':
            medicine_id = request.POST.get("medicine_id", "")
            try:
                medicine = Medicine.objects.get(id=medicine_id)
                medicine.delete()
            except:
                pass
            return HttpResponse('')

@login_required()
def stop_medicine(request):
    logged_user_profile = request.user.get_profile()
    if logged_user_profile.is_doctor():
        if request.method == 'POST':
            medicine_id = request.POST.get("medicine_id", "")
            try:
                medicine = Medicine.objects.get(id=medicine_id)
                medicine.date = datetime.now()
                medicine.save()
            except:
                pass
            return HttpResponse('')


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



        

############################## REPORTS ########################################
@login_required
@only_doctor_consulting
def view_report(request, id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    patient = task.patient.get_profile()
    marks = task.get_variables_mark()
    beck_mark = task.calculate_beck_mark()
    hamilton_mark, hamilton_submarks = task.calculate_hamilton_mark()
    dimensions = task.get_dimensions_mark()
    ave_mark = task.calculate_mark_by_code('AVE')
    light_mark = task.calculate_mark_by_code('L')
    blaxter_mark = task.calculate_mark_by_code('AS')
    medicines = Medicine.objects.filter(patient=task.patient,
    appointment=task.appointment, is_previous=False).order_by('-date')

    try:
        recurrent = beck_mark > 13 and task.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(code__in=['AP4','AP5','AP6'])
        recurrent = recurrent or (hamilton_mark > 18 and task.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(code__in=['AP1','AP3']))
    except:
        recurrent = None
    try:
        h6 = hamilton_submarks['H6']
    except:
        h6 = None

    conclusions = Conclusion.objects.filter(appointment=task.appointment)
    data = {'task': task,
            'marks': marks,
            'patient': patient,
            'conclusions':conclusions,
            'beck_mark':beck_mark,
            'beck_scale':task.get_depression_status(),
            'hamilton_mark':hamilton_mark,
            'hamilton_scale': task.get_anxiety_status(),
            'dimensions': dimensions,
            'h6_mark': h6,
            'ave_mark':ave_mark,
            'ave_status':task.get_ave_status(),
            'recurrent':recurrent,
            'light_mark':light_mark,
            'blaxter_mark':blaxter_mark,
            'as_mark':task.calculate_mark_by_code('AS'),
            'treatment':medicines
            }

    if request.GET and request.GET.get('as', '') == 'pdf':
        mypdf = PDFTemplateView()
        mypdf.request=request
        mypdf.filename ='Consulting30_report.pdf'
        mypdf.header_template = 'ui/includes/pdf_header.html'
        mypdf.template_name='consulting/consultation/report/base.html'
        data.update({'as_pdf':True})
        return mypdf.render_to_response(context=data)
    else:
        return render_to_response('consulting/consultation/report/base.html',
                                data,
                                context_instance=RequestContext(request))


@login_required()
@paginate(template_name='consulting/patient/list_reports.html',
    list_name='reports', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_reports(request):
    logged_user_profile = request.user.get_profile()

    patient_user_id = request.session['patient_user_id']

    if logged_user_profile.is_doctor():
        patient_user = User.objects.get(id=patient_user_id)

        reports = Task.objects.filter(patient=patient_user,survey__id__in=[settings.PREVIOUS_STUDY, settings.INITIAL_ASSESSMENT, settings.ANXIETY_DEPRESSION_SURVEY], completed=True).order_by('-end_date')

        template_data = {}
        template_data.update({'patient_user': patient_user,
                                'reports': reports,
                                'patient_user_id': patient_user_id,
                                'csrf_token': get_token(request)})
        return template_data
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

@login_required()
@paginate(template_name='consulting/patient/list_reports.html',
    list_name='reports', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_provisional_reports(request, id_appointment, code_illness):
    logged_user_profile = request.user.get_profile()

    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    illness = get_object_or_404(Illness, code=int(code_illness))

    if logged_user_profile.is_doctor():
        patient_user = appointment.patient

        reports = Task.objects.filter(patient=patient_user,appointment=appointment, completed=True).order_by('-end_date')

        template_data = {}
        template_data.update({'patient_user': patient_user,
                                'reports': reports,
                                'appointment': appointment,
                                'illness': illness,
                                'patient_user_id': patient_user.id,
                                'csrf_token': get_token(request)})
        return template_data
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

@login_required()
@paginate(template_name='consulting/patient/list_messages.html',
    list_name='messages', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_messages(request):
    logged_user_profile = request.user.get_profile()

    patient_user_id = request.session['patient_user_id']

    if logged_user_profile.is_doctor():
        patient_user = User.objects.get(id=patient_user_id)

        messages = Message.objects.filter(Q(parent__isnull=True), Q(recipient=patient_user) | Q(author=patient_user)).order_by('-sent_at')

        template_data = {}
        template_data.update({'patient_user': patient_user,
                                'messages': messages,
                                'patient_user_id': patient_user_id,
                                'csrf_token': get_token(request)})
        return template_data
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@paginate(template_name='consulting/patient/list_recommendations.html',
    list_name='recommendations', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_recommendations(request):
    logged_user_profile = request.user.get_profile()

    patient_user_id = request.session['patient_user_id']

    if logged_user_profile.is_doctor():
        patient_user = User.objects.get(id=patient_user_id)

        recommendations = Conclusion.objects.filter(patient=patient_user).exclude(recommendation__exact="").order_by('-date')

        template_data = {}
        template_data.update({'patient_user': patient_user,
                                'recommendations': recommendations,
                                'patient_user_id': patient_user_id,
                                'csrf_token': get_token(request)})
        return template_data
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

@login_required()
@only_doctor_consulting
def user_evolution(request):
    logged_user_profile = request.user.get_profile()

    patient_user_id = request.session['patient_user_id']
    limit = 6
    patient_user = User.objects.get(id=patient_user_id)
    date_filter = Q(end_date__lte=datetime.now())
    form = ParametersFilterForm()
    if request.method == 'POST':
        form = ParametersFilterForm(request.POST)
        if form.is_valid():
            to_date = form.cleaned_data['to_date'] and form.cleaned_data['to_date']+timedelta(days=1) or datetime.now()
            from_date = form.cleaned_data['from_date']
            if from_date:
                date_filter = Q(end_date__gte=from_date, end_date__lte=to_date)
            else:
                date_filter = Q(end_date__lte=to_date)
            limit = None

    tasks = Task.objects.filter(Q(patient=patient_user,survey__id__in=[settings.ANXIETY_DEPRESSION_SURVEY, settings.INITIAL_ASSESSMENT], completed=True),date_filter).order_by('-end_date')[:limit]

    latest_marks = {}
    latest_dimensions = {}
    scales = {'beck':[],'hamilton':[]}
    vticks = []
    for t in tasks:
        marks = t.get_variables_mark()
        dimensions = t.get_dimensions_mark(marks)
        for name, value in dimensions.items():
            if name in latest_dimensions:
                latest_dimensions[name].insert(0,[t.end_date, value])
            else:
                latest_dimensions[name] = [[t.end_date, value]]
        for var, mark in marks.items():
            if mark != None:
                if var.name in latest_marks.keys():
                    latest_marks[var.name].insert(0, [t.end_date, mark])
                else:
                    latest_marks[var.name] = [[t.end_date, mark]]
            if not t.end_date in vticks:
                vticks.append(t.end_date)
        scales['beck'].insert(0, [t.end_date, t.calculate_beck_mark()])
        scales['hamilton'].insert(0, [t.end_date, t.calculate_hamilton_mark()[0]])

    vticks.sort()

    tasks = Task.objects.filter(Q(patient=patient_user,survey__id__in=[settings.ADHERENCE_TREATMENT], completed=True),date_filter).order_by('-end_date')[:limit]
    values = {}
    tticks = []
    mindate = maxdate = datetime.now()
    for t in tasks:
        mindate = t.end_date < mindate and t.end_date or mindate
        maxdate = t.end_date > maxdate and t.end_date or maxdate
        for a in t.get_answers():
            if a.question.code in values:
                values[a.question.code].append((t.end_date, a.weight))
            else:
                values[a.question.code] =[(t.end_date, a.weight),]
        tticks = [mindate, maxdate]


    return render_to_response('consulting/patient/user_evolution.html', 
                                {'patient_user':patient_user,
                                 'form': form,
                                 'latest_marks': latest_marks,
                                 'latest_dimensions': latest_dimensions,
                                 'scales': scales,
                                 'values': values,
                                 'active_tab': (request.POST.get('active_tab','')).replace('#',''),
                                 'ticks_variables':vticks,
                                 'ticks_treatment':tticks},
                            context_instance=RequestContext(request))

@login_required()
@only_doctor_consulting
def save_notes(request):
    if request.POST and request.POST.get('name','')=='notes':
        request.session["notes"] = request.POST.get('value')
        return HttpResponse('')
    return HttpResponse('Error')

