# -*- encoding: utf-8 -*-
import os
import time
import operator
import xlwt
import json
import cStringIO
import random
import string
import json
import hashlib
import requests

from datetime import time as ttime
from datetime import date, timedelta, datetime
from random import randint
from itertools import chain
from decorators import *

from django.views.decorators.cache import never_cache
from django.middleware.csrf import get_token
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.utils import simplejson, formats
from django.utils.translation import ugettext as _
from django.db.models import Q, Max
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import send_mail

from userprofile.models import Profile
from medicament.models import Component, Group
from consulting.models import Medicine, Task, Conclusion, Result, Answer, Alert
from cal.models import Appointment, Slot, SlotType, Payment
from illness.models import Illness
from survey.models import Survey, Block, Question, Option, Template
from formula.models import Variable, Formula, Scale
from private_messages.models import Message

from userprofile.forms import ProfileForm, ProfileSurveyForm
from userprofile.forms import ProfileFiltersForm
from consulting.forms import MedicineForm, TreatmentForm
from consulting.forms import ConclusionForm
from consulting.forms import SelectSurveyForm
from consulting.forms import SelectSurveyTaskForm
from consulting.forms import SelfRegisterForm
from consulting.forms import SelectNotAssessedVariablesForm
from consulting.forms import SymptomsWorseningForm, ParametersFilterForm
from illness.forms import IllnessSelectionForm
from survey.forms import QuestionsForm
from cal.forms import AppointmentForm, DoctorSelectionForm, PaymentForm

from cal.views import scheduler, app_add

from consulting.helper import strip_accents
from consulting.templatetags.consulting import sexify

from cal.utils import create_calendar
from cal.utils import mnames
from cal.utils import check_vacations
from cal.utils import get_doctor_preferences
from cal.utils import add_minutes

from wkhtmltopdf.views import *


#################################### INDEX ####################################
@login_required()
def index(request):
    try:
        logged_user_profile = request.user.get_profile()
    except:
        if request.user.is_staff:
            return HttpResponseRedirect('/admin/')
        else:
            HttpResponseRedirect(reverse('registration_logout'))

    if logged_user_profile.role == settings.DOCTOR:
        return render_to_response('consulting/doctor/index_doctor.html', {},
                                  context_instance=RequestContext(request))
    elif logged_user_profile.role == settings.ADMINISTRATIVE:
        return render_to_response(
                    'consulting/administrative/index_administrative.html', {},
                    context_instance=RequestContext(request))
    elif logged_user_profile.role == settings.PATIENT:
        return render_to_response('consulting/patient/index_patient.html',
                                  {'patient_user': request.user.get_profile()},
                                  context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def keep_alive(request, timeout):
    if not int(timeout):
        request.session.set_expiry(settings.SESSION_COOKIE_AGE)
        request.session['timeout'] = settings.SESSION_COOKIE_AGE
        return HttpResponse('')
    if (int(timeout) <= 7200 and int(timeout) >= settings.SESSION_COOKIE_AGE):
        request.session.set_expiry(int(timeout))
        request.session['timeout'] = int(timeout)
        return HttpResponse('')

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
            mlst.append(dict(n=n + 1, name=month, slot=slot, current=current))
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
        events = Appointment.objects.filter(doctor=doctor,
                                            date__year=year,
                                            date__month=month,
                                            date__day=day,
                                            status=settings.CONFIRMED
                                           ).order_by('start_time')
    else:
        events = Appointment.objects.none()

    lst = create_calendar(int(year), int(month), doctor=request.user)

    available, free_intervals = Appointment.objects.availability(
                doctor,
                date(int(year), int(month), int(day)))

    template_data = dict(year=year,
                         month=month,
                         day=day,
                         user=request.user,
                         month_days=lst,
                         mname=mnames[int(month) - 1],
                         events=events,
                         free_intervals=free_intervals,
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

    return render_to_response("cal/includes/calendar.html",
                              dict(year=year,
                                   month=month,
                                   user=request.user,
                                   month_days=lst,
                                   mname=mnames[month - 1]),
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
                request.session["notes"] = ''
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


def check_task_completion(request, task):
    answers = task.get_answers()
    if not answers:
        return False  
    if task.treated_blocks.count() < task.survey.num_blocks(task.kind):
        return False
    questions = task.questions.filter(required=True)
    if task.self_administered:
        if task.treated_blocks.count() >= 2:
            questions = chain(questions, Question.objects.filter(required=True,kind__in=(0, task.patient.get_profile().sex), questions_categories__categories_blocks__kind__in=(settings.GENERAL, task.kind), questions_categories__categories_blocks__in=task.treated_blocks.all().exclude(code=settings.ANXIETY_DEPRESSION_BLOCK)))
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

    if 'cronos' in request.session:
        warn_external_service(request, task)

    return True

def warn_external_service(request, task):
    payload = {'method':'nuevoCuestionario'}
    payload['nuhsa'] = task.patient.get_profile().medical_number
    payload['id'] = task.id
    payload['nombre'] = task.survey.name
    if task.survey.is_reportable:
        payload['url'] = request.build_absolute_uri(reverse('cronos_view_report', args=[task.id])+'?as=pdf&token='+hashlib.md5(payload['nuhsa']).hexdigest())
        payload['tipo'] = 'PDF'
    else:
        payload['url'] = ''
        payload['tipo'] = ''
    #payload['timestamp'] = int(time.mktime(datetime.now().timetuple())*1000)
    payload['timestamp'] = formats.date_format(datetime.now(), "SHORT_DATETIME_FORMAT")
    risk = task.check_risks()
    if risk:
        payload['riesgo'] = risk.name
    else:
        payload['riesgo'] = ''
    print payload
    r = requests.post(settings.AT4_SERVER+settings.AUTH_RESOURCE, data=payload, verify=False)
    print r.text

 

def new_result_sex_status(id_logged_user, id_task, id_appointment):
    logged_user = get_object_or_404(User, pk=int(id_logged_user))
    task = get_object_or_404(Task, pk=int(id_task))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    profile = task.patient.get_profile()
    my_block = get_object_or_404(Block, code=int(settings.ADMINISTRATIVE_DATA))

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
        status_option = get_object_or_404(Option,
                                          code=settings.CODE_STABLE_PARTNER)
    elif status == settings.DIVORCED:
        status_option = get_object_or_404(Option, code=settings.CODE_DIVORCED)
    elif status == settings.WIDOW_ER:
        status_option = get_object_or_404(Option, code=settings.CODE_WIDOW_ER)
    elif status == settings.SINGLE:
        status_option = get_object_or_404(Option, code=settings.CODE_SINGLE)
    elif status == settings.OTHER:
        status_option = get_object_or_404(Option, code=settings.CODE_OTHER)

    #UPDATE RESULT
    answer = Answer(result=result,
                    option=sex_option,
                    question=sex_option.question)
    answer.save()
    answer = Answer(result=result,
                    option=status_option,
                    question=status_option.question)
    answer.save()
    result.save()
    return result


@login_required()
@only_doctor_consulting
def administrative_data(request, id_task, code_block=None, code_illness=None,
                        id_appointment=None):
    task = get_object_or_404(Task, pk=int(id_task))
    user = task.patient
    profile = user.get_profile()
    block = get_object_or_404(Block, code=int(code_block))

    treated_blocks = task.treated_blocks.all()

    # CHECK IF DOCTOR CONTAINS THIS PATIENT
    if not user.get_profile().doctor == request.user:
        return HttpResponseRedirect(reverse('consulting_index'))

    if request.method == "POST":
        exclude_list = ['user', 'role', 'doctor',
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

            if (name != name_form or
                first_surname != first_surname_form or
                nif != nif_form) or \
               (nif_form == '' and dob != dob_form):
                #NUEVO username
                username = generate_username(form)
                profile.user.username = username
                profile.user.save()

                profile.save()
                result = new_result_sex_status(request.user.id, 
                                               task.id,
                                               id_appointment)

                if block not in treated_blocks:
                    task.treated_blocks.add(block)

                if check_task_completion(request, task):
                    task.completed = True
                    task.end_date = datetime.now()
                    task.save()

                #SEN EMAIL to warn new username
                if user.email:
                    sendemail(user)
                available_blocks = task.survey.blocks.filter(code__gt=code_block, kind__in=(settings.GENERAL, task.kind)).order_by('code')
                if available_blocks:
                    n_block = available_blocks[0].code
                else:
                    n_block = 9999
                return render_to_response(
                                    'consulting/consultation/warning.html',
                                    {'patient_user': user,
                                    'task': task,
                                    'code_illness': code_illness,
                                    'id_appointment': id_appointment,
                                    'next_block': n_block},
                                    context_instance=RequestContext(request))
            else:
                profile.save()
                result = new_result_sex_status(request.user.id,
                                               task.id,
                                               id_appointment)

                if block not in treated_blocks:
                    task.treated_blocks.add(block)

                if check_task_completion(request, task):
                    task.completed = True
                    task.end_date = datetime.now()
                    task.save()

                return next_block(task, block, code_illness, id_appointment)
        else:
            return render_to_response(
                            'consulting/patient/patient.html',
                            {'form': form,
                            'patient_user': user,
                            'task': task,
                            'code_illness': code_illness,
                            'id_appointment': id_appointment,
                            'my_block': block},
                            context_instance=RequestContext(request))
    else:
        exclude_list = ['user', 'role', 'doctor',
                        'illnesses']

        if user.is_active:
            active = settings.ACTIVE
        else:
            active = settings.DEACTIVATE

        form = ProfileSurveyForm(instance=profile, exclude_list=exclude_list,
                                 initial={'active': active})

    return render_to_response('consulting/patient/patient.html',
                              {'form': form,
                               'patient_user': user,
                               'task': task,
                               'id_appointment': id_appointment,
                               'my_block': block},
                              context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def show_task(request, id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    return render_to_response('consulting/consultation/task.html',
                              {'task':task},
                              context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def show_block(request, id_task, code_block=None, code_illness=None,
               id_appointment=None):
    task = get_object_or_404(Task, pk=int(id_task))
    if not task.assess:
        return resume_task(request, id_appointment, code_illness, id_task)
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    request.session['patient_user_id'] = appointment.patient.id
    if task.survey.code == settings.SELF_REGISTER:
        return self_register(request, id_task, id_appointment, code_illness)
    elif code_block is None or code_block == str(0):
        block = task.survey.blocks.filter(kind__in=(settings.GENERAL,task.kind)).order_by('code')[0]
        return HttpResponseRedirect(
                            reverse('consulting_show_task_block',
                                    kwargs={'id_task': task.id,
                                            'code_block': block.code,
                                            'code_illness': code_illness,
                                            'id_appointment': id_appointment}))
    elif code_block == str(settings.ADMINISTRATIVE_DATA):
        return administrative_data(request, id_task=id_task,
                                   code_block=code_block,
                                   code_illness=code_illness,
                                   id_appointment=id_appointment)
    else:
        block = get_object_or_404(Block, code=code_block,
                                  kind__in=(settings.GENERAL, task.kind))
    treated_blocks = task.treated_blocks.all()
    dic = {}
    questions = task.questions.all()
    if not questions or int(code_block) != settings.ANXIETY_DEPRESSION_BLOCK:
        categories = block.categories.all().order_by('id')
        for category in categories:
            questions = category.questions.filter(kind__in=[settings.UNISEX, task.patient.get_profile().sex]).order_by('id')
            for question in questions:
                options = question.question_options.all().order_by('id')
                dic[question] = [(option.id, sexify(option.text,task.patient))for option in options]
    else:
        for question in questions:
            options = question.question_options.all().order_by('id')
            dic[question] = [(option.id, sexify(option.text,task.patient)) for option in options]
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
                    field = name_field[:name_field.find('_value')]
                    answers[field] = values
                else:
                    items[name_field] = values
            for name_field, values in items.items():
                question = Question.objects.get(code=name_field)
                if name_field in answers.keys():
                    val = answers[name_field]
                else:
                    val = None
                if isinstance(values, list):
                    for value in values:
                        if value.isdigit():
                            option = Option.objects.get(pk=int(value))
                        else:
                            val = value
                        answer = Answer(result=new_result, option=option,            value=val, question=option.question)
                        answer.save()
                elif values.isdigit() and question and question.question_options.filter(pk=int(values)).exists():
                    option = Option.objects.get(pk=int(values))
                    answer = Answer(result=new_result, option=option,
                                    value=val, question=option.question)
                    answer.save()
                elif values:
                    answer = Answer(result=new_result, value=values,
                                    question=Question.objects.get(code=name_field))
                    answer.save()

            if block not in treated_blocks:
                task.treated_blocks.add(block)
            if not task.start_date:
                task.start_date = datetime.now()
            task.updated_at = datetime.now()
            if check_task_completion(request, task):
                task.completed = True
                task.appointment = appointment
                task.end_date = datetime.now()
                task.assess = False
                task.clear_cache()
                update_risks = True
            else:
                task.completed = False
                task.end_date = None
            task.save()

            if task.completed and update_risks:
                risk = task.patient.get_profile().check_risks()
                if risk:
                    Alert.objects.create(task=task, risk=risk)

            return next_block(task, block, code_illness, id_appointment)

    last_result = None
    try:
        last_result = task.task_results.filter(block=block).latest('date')
        selected_options = Answer.objects.select_related('option').filter(result=last_result)

    except:
        if code_block == str(settings.PRECEDENT_RISK_FACTOR):
            try:
                last_result =  Result.objects.filter(block=block,
                    patient=task.patient).latest('date')
                selected_options = Answer.objects.select_related('option').filter(result=last_result)
            except:
                selected_options = []
        else:
            selected_options = []
    form = QuestionsForm(dic=dic, selected_options=selected_options)

    return render_to_response('consulting/consultation/block.html',
                              {'form': form,
                               'task': task,
                               'result': last_result,
                               'appointment': appointment,
                               'my_block': block,
                               'patient_user': task.patient},
                              context_instance=RequestContext(request))


def next_block(task, block, code_illness, id_appointment):
    available_blocks = task.survey.blocks.filter(code__gt=block.code, kind__in=(settings.GENERAL, task.kind)).order_by('code')
    if available_blocks:
        return HttpResponseRedirect(
                            reverse('consulting_show_task_block',
                                    kwargs={'id_task': task.id,
                                            'code_block': available_blocks[0].code, 
                                            'code_illness': code_illness,
                                            'id_appointment': id_appointment
                                            }))
    elif (task.self_administered and
          code_illness == str(settings.DEFAULT_ILLNESS)):
        task.previous_days = 0
        task.save()
        return HttpResponseRedirect(
                            reverse('consulting_finished_task',
                                    kwargs={'id_task': task.id,
                                            'code_illness': code_illness,
                                            'id_appointment': id_appointment
                                            }))
    elif task.self_administered and not block.code == settings.BEHAVIOR_BLOCK:
        task.previous_days = 0
        task.save()
        return HttpResponseRedirect(
                            reverse('consulting_show_task_block',
                                    kwargs={'id_task': task.id,
                                            'code_block': settings.BEHAVIOR_BLOCK,
                                            'code_illness': code_illness, 
                                            'id_appointment': id_appointment
                                            }))
    elif task.completed:
        return HttpResponseRedirect(
                            reverse('consulting_finished_task',
                                    kwargs={'id_task': task.id,
                                            'code_illness': code_illness,
                                            'id_appointment': id_appointment
                                            }))
    else:
        return HttpResponseRedirect(
                            reverse('consulting_main',
                                    kwargs={'code_illness': code_illness,
                                            'id_appointment': id_appointment
                                            }))


@login_required()
@only_patient_consulting
def self_administered_block(request, id_task):
    task = get_object_or_404(Task, pk=int(id_task), assess=True,
                             completed=False,
                             patient__id=request.user.id,
                             self_administered=True)

    if task.survey.code == settings.SELF_REGISTER:
        return HttpResponseRedirect(reverse('consulting_self_register', 
                                            args=[task.id]))
        pass
    if task.task_results.all():
        last_result = task.task_results.latest('date')

        if last_result:
            selected_options = Answer.objects.select_related('option').filter(result=last_result)
    else:
        selected_options = []

    dic = {}
    treated_blocks = task.treated_blocks.all()
    blocks = task.survey.blocks.filter(kind=task.kind)
    questions = task.questions.all()
    if questions:
        for question in questions:
            options = question.question_options.all().order_by('id')
            dic[question] = [
                             (option.id, sexify(option.text,task.patient)) for option in options]
    if blocks:
        block = blocks[0]
        if not questions:
            categories = block.categories.all().order_by('id')

            for category in categories:
                questions = category.questions.all().order_by('id')
                for question in questions:
                    options = question.question_options.all().order_by('id')
                    dic[question] = [
                                    (option.id, sexify(option.text,task.patient))for option in options]

    if request.method == 'POST':
        form = QuestionsForm(request.POST, dic=dic,
                             selected_options=selected_options)

        if form.is_valid():
            result = Result(patient=task.patient, survey=task.survey,
                            task=task, block=block, created_by=request.user)
            result.save()

            if task.task_results.count() == 1:
                task.start_date = result.date
                task.save()

            items = form.cleaned_data.items()
            for name_field, values in items:
                if isinstance(values, list):
                    for value in values:
                        option = Option.objects.get(pk=int(value))
                        answer = Answer(result=result, option=option,
                                        question=option.question)
                        answer.save()
                elif values.isdigit():
                    option = Option.objects.get(pk=int(values))
                    answer = Answer(result=result, option=option,
                                    question=option.question)
                    answer.save()
                elif values:
                    answer = Answer(result=result, value=values, 
                                    question=Question.objects.get(code=name_field))
                    answer.save()

            if block not in treated_blocks:
                task.treated_blocks.add(block)

            if check_task_completion(request, task):
                task.completed = True
                task.end_date = datetime.now()
                task.save()

            if block.code == settings.VIRTUAL_BLOCK:
                return HttpResponseRedirect(reverse('consulting_list_surveys'))
            else:
                return HttpResponseRedirect(
                    reverse('consulting_symptoms_worsening', args=[task.id]))
    else:
        form = QuestionsForm(dic=dic, selected_options=selected_options)

    return render_to_response('consulting/patient/surveys/block.html',
                              {'form': form,
                               'task': task},
                              context_instance=RequestContext(request))


@login_required()
def self_register(request, id_task, id_appointment=None, code_illness=None):
    if request.user.get_profile().is_doctor():
        task = get_object_or_404(Task, pk=int(id_task), assess=True)
    else:
        task = get_object_or_404(Task, pk=int(id_task), assess=True,
                                 completed=False,
                                 patient__id=request.user.id,
                                 self_administered=True)
    if request.method == 'POST':
        form = SelfRegisterForm(request.POST)
        if form.is_valid():
            task.observations = form.cleaned_data['table']
            if not task.start_date:
                task.start_date = datetime.now()
            task.save()
            if request.user.get_profile().is_doctor():
                return HttpResponseRedirect(reverse('consulting_list_self_administered_tasks', kwargs={'code_illness': code_illness, 'id_appointment': id_appointment}))
            else:
                return HttpResponseRedirect(reverse('consulting_list_surveys'))
        else:
            return render_to_response(
                            'consulting/patient/surveys/self_register.html',
                            {'form': form,
                             'data': request.POST.get(['table'],task.observations),
                             'task': task},
                            context_instance=RequestContext(request))
    else:
        form = SelfRegisterForm()
        return render_to_response(
                'consulting/patient/surveys/self_register.html',
                {'form': form,
                'data': task.observations,
                'task': task},
                context_instance=RequestContext(request))


@login_required()
@only_patient_consulting
def symptoms_worsening(request, id_task):
    task = get_object_or_404(Task, pk=int(id_task), assess=True,
                             patient__id=request.user.id,
                             self_administered=True)
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
@never_cache
def monitoring(request, id_appointment, code_illness=None):
    if 'cronos' in request.session and request.session['cronos']:
        return HttpResponseRedirect(reverse('cronos_tasks'))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    temp = []
    previous = False
    tasks = Task.objects.filter(appointment=appointment)
    if not code_illness or appointment.date < date.today():
        illness = None
    else:
        illness = get_object_or_404(Illness, code=code_illness)
        if not tasks.count():
            previous = True
            latest_tasks = {}
            tasks = Task.objects.filter(
                patient=appointment.patient,
                completed=True,
                survey__surveys_illnesses__code=code_illness
            ).order_by('-end_date')
            for t in tasks:
                if not t.survey in latest_tasks or t.end_date > latest_tasks[t.survey].end_date:
                    latest_tasks[t.survey] = t
            tasks = latest_tasks.values()



    medicaments_list = Medicine.objects.filter(appointment=appointment,
                                               date__isnull=True,
                                               is_previous=False)
    try:
        conclusions = Conclusion.objects.filter(appointment=appointment)
    except:
        conclusions = Conclusion.objects.none()
    return render_to_response(
                'consulting/consultation/monitoring/index.html',
                {'patient_user': appointment.patient,
                'patient_user_id': appointment.patient.id,
                'appointment': appointment,
                'illness': illness,
                'treatment': medicaments_list,
                'conclusions': conclusions,
                'previous': previous,
                'tasks': tasks},
                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
@paginate(
    template_name='consulting/consultation/monitoring/incomplete_surveys/list.html',
    list_name='tasks', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_incomplete_tasks(request, id_appointment, code_illness,
                          self_administered=False):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    illness = get_object_or_404(Illness, code=code_illness)
    patient = appointment.patient
    tasks = Task.objects.filter(Q(patient=patient,
                                  survey__surveys_illnesses__code=code_illness)
                                & Q(self_administered=self_administered,
                                    assess=True)).order_by('-creation_date')

    template_data = {}
    template_data.update({'patient_user': patient,
                          'tasks': tasks,
                          'appointment': appointment,
                          'illness': illness,
                          'csrf_token': get_token(request)})
    return template_data


@login_required()
@only_doctor_consulting
def not_assess_task(request, id_task, id_appointment):
    task = get_object_or_404(Task, pk=int(id_task))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))

    task.assess = False
    task.completed = ((task.survey.code == settings.SELF_REGISTER)
                      or task.completed)
    if task.completed:
        task.appointment = appointment
    task.end_date = datetime.now()
    task.save()

    return HttpResponse('Tarea marcada correctamente')


@login_required()
@only_doctor_consulting
def resume_task(request, id_appointment, code_illness, id_task):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    task = get_object_or_404(Task, pk=int(id_task))
    if code_illness and code_illness != '0':
        illness = get_object_or_404(Illness, code=code_illness)
    else:
        illness = Illness.objects.none()
    if task.treated_blocks.filter(is_scored=True).exists():
        tasks = Task.objects.filter(patient=task.patient, survey=task.survey,
                                    completed=True).order_by('-end_date')[:5]

        values = {}

        mindate = tasks[0].end_date
        maxdate = tasks[0].end_date
        for t in tasks:
            mindate = t.end_date < mindate and t.end_date or mindate
            maxdate = t.end_date > maxdate and t.end_date or maxdate
            variables = t.get_variables_mark()
            for var, mark in variables.items():
                if var in values:
                    values[var].insert(0, (t, mark))
                else:
                    values[var] =[(t, mark), ]
        ticks = (mindate, maxdate)

        

        extra_template = ''
        if task.survey.code == settings.OCIR_SURVEY:
            extra_template = 'consulting/consultation/report/ocir.html'

        return render_to_response(
            'consulting/consultation/monitoring/evolution.html',
            {'values': values,
             'task': task,
             'ticks': ticks,
             'appointment': appointment,
             'extra_info': extra_template,
             'illness': illness,
             'patient_user': appointment.patient},
            context_instance=RequestContext(request))
    else:
        return render_to_response(
            'consulting/consultation/monitoring/task_details.html',
            {'task': task,
             'appointment': appointment,
             'illness': illness,
             'patient_user': appointment.patient},
            context_instance=RequestContext(request))


@only_doctor_consulting
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
        form = SelectNotAssessedVariablesForm(request.POST,
                                              variables=variables)
        if form.is_valid():
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
            task.previous_days = 0
            task.save()
            return HttpResponseRedirect('')
    else:
        form = SelectNotAssessedVariablesForm(variables=variables)

    return render_to_response(
                'consulting/consultation/monitoring/incomplete_surveys/select_not_assessed_variables.html',
                {'form': form,
                'patient_user': task.patient},
                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def select_successive_survey(request, id_appointment, code_illness=None):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    illness = get_object_or_404(Illness, code=code_illness)
    templates = Template.objects.all().order_by('-updated_at')
    variables = None
    tasks = Task.objects.filter(
    Q(patient=appointment.patient, completed=True,
        survey__surveys_illnesses__code=code_illness, survey__code__in=(settings.ANXIETY_DEPRESSION_SURVEY, settings.INITIAL_ASSESSMENT))).order_by('-end_date')
    for t in tasks:
        tmp_vars = t.get_list_variables(settings.DEFAULT_NUM_VARIABLES)
        if tmp_vars:
            variables = tmp_vars
            break
    #NEW
    ClassForm = SelectSurveyForm

    if request.method == 'POST':
        if variables is None:
            form = ClassForm(request.POST, illness=illness)
        else:
            form = ClassForm(request.POST, illness=illness, 
                             variables=variables)
        if form.is_valid():
            code_survey = form.cleaned_data['survey']
            if 'kind' in form.cleaned_data:
                kind = form.cleaned_data['kind']
            else:
                kind = settings.GENERAL

            print code_survey
            if code_survey == str(settings.CUSTOM):
                survey = get_object_or_404(Survey, code=int(settings.ANXIETY_DEPRESSION_SURVEY))
            else:
                survey = get_object_or_404(Survey, code=int(code_survey))

            observations = ""
            if code_survey == str(settings.SELF_REGISTER):
                observations = form.cleaned_data['table']
                kind = settings.GENERAL
                if not Template.objects.filter(template=observations).count():
                    template = Template()
                    template.created_by = request.user
                    template.template = observations
                    template.save()

            task = Task(created_by=request.user,
                        patient=appointment.patient,
                        appointment=appointment,
                        self_administered=False,
                        survey=survey,
                        kind=kind,
                        observations=observations)
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
                                kwargs={'id_task': task.id, 
                                        'id_appointment': id_appointment,
                                        'code_illness': code_illness,
                                        'code_block': 0}))
    else:
        if variables is None:
            form = ClassForm(illness=illness)
        else:
            form = ClassForm(variables=variables, illness=illness)
            if Task.objects.filter(survey__code=int(settings.INITIAL_ASSESSMENT),
                                   patient=appointment.patient,
                                   created_by=appointment.doctor
                                   ).count() != 0:
                for choice in form.fields['survey'].choices:
                    if choice[0] == settings.INITIAL_ASSESSMENT:
                        form.fields['survey'].choices.remove(choice)
                        break

    return render_to_response(
            'consulting/consultation/monitoring/select_survey.html',
            {'form': form,
            'appointment': appointment,
            'illness': illness,
            'templates': templates,
            'code_variables': settings.CUSTOM,
            'code_self_register': settings.SELF_REGISTER,
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



@login_required
@only_doctor_consulting
@never_cache
def conclusion_monitoring(request, id_appointment, code_illness):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    illness= get_object_or_404(Illness, code=code_illness)
    try:
        conclusion = Conclusion.objects.get(appointment=appointment)
    except:
        conclusion = Conclusion()

    if request.method == 'POST':
        form = ConclusionForm(request.POST, instance=conclusion)
        if form.is_valid():
            conclusion = form.save(commit=False)
            conclusion.created_by = request.user
            conclusion.patient = appointment.patient
            conclusion.appointment = appointment
            conclusion.save()

            return HttpResponseRedirect(
                                reverse('consulting_main',
                                        kwargs={'id_appointment':id_appointment,'code_illness':code_illness}))
    else:
        if not conclusion.observation and 'notes' in request.session:
            conclusion.observation=request.session["notes"]
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
    illness= get_object_or_404(Illness, code=code_illness)
    request.session['appointment'] = appointment
    request.session['illness'] = illness
    patient_user = appointment.patient
    return scheduler(request, patient_user.id)


@login_required()
@only_doctor_consulting
def select_self_administered_survey_monitoring(request, id_appointment, code_illness='CR'):
    illness = get_object_or_404(Illness, code=code_illness)
    templates = Template.objects.all().order_by('-updated_at')
    variables = []
    if id_appointment:
        appointment = get_object_or_404(Appointment, pk=int(id_appointment))
        tasks = Task.objects.filter(
        Q(patient=appointment.patient, completed=True,
            survey__surveys_illnesses__code=code_illness, survey__code__in=(settings.ANXIETY_DEPRESSION_SURVEY, settings.INITIAL_ASSESSMENT))).order_by('-end_date')
        for t in tasks:
            tmp_vars = t.get_list_variables(settings.DEFAULT_NUM_VARIABLES, exclude=['V28'])
            if tmp_vars:
                variables = tmp_vars
                break
    else:
        appointment = None


    if request.method == 'POST':
        form = SelectSurveyTaskForm(request.POST, variables=variables, illness=illness)


        if form.is_valid():
            code_survey = form.cleaned_data['survey']
            previous_days = form.cleaned_data['previous_days']
            try:
                kind = form.cleaned_data['kind']
                exc_block = get_object_or_404(Block,code=settings.BEHAVIOR_BLOCK, kind=kind)
            except:
                kind = settings.GENERAL
                exc_block = get_object_or_404(Block,code=settings.BEHAVIOR_BLOCK, kind=settings.EXTENSO)
            if code_survey == str(settings.CUSTOM):
                survey = get_object_or_404(Survey,
                                code=settings.ANXIETY_DEPRESSION_SURVEY)
            else:
                survey = get_object_or_404(Survey,
                                code=code_survey)
            observations = ""
            if code_survey == str(settings.SELF_REGISTER):
                observations = form.cleaned_data['table']
                kind = settings.GENERAL
                if not Template.objects.filter(template=observations).count():
                    template = Template()
                    template.created_by = request.user
                    template.template = observations
                    template.save()

            if previous_days:
                task = Task(created_by=request.user, 
                            patient=appointment.patient,
                            appointment=None, 
                            self_administered=True, 
                            survey=survey,
                            previous_days=previous_days,
                            kind=kind,
                            observations=observations)
                task.save()
            else:
                from_date = form.cleaned_data['from_date']
                to_date  = form.cleaned_data['to_date']
                repeat = form.cleaned_data['repeat']
                if to_date and not repeat is None:
                    delta = timedelta(days=max(0, repeat*7-1))
                    end = from_date
                    for w in range((to_date-from_date).days/max(1, repeat*7)):
                        std, end = end, end+delta
                        if end > to_date:
                            end = to_date
                        task = Task(created_by=request.user,
                                patient=appointment.patient,
                                appointment=None,
                                self_administered=True,
                                survey=survey,
                                from_date=std,
                                to_date=end,
                                kind=kind,
                                observations=observations)
                        end = end+timedelta(days=1)
                        task.save()

                else:
                    task = Task(created_by=request.user,
                                patient=appointment.patient,
                                appointment=None,
                                self_administered=True,
                                survey=survey,
                                from_date=from_date,
                                to_date=to_date,
                                kind=kind,
                                observations=observations)
                    task.save()
            
            if variables:
                id_variables = form.cleaned_data['variables']
            else:
                id_variables = None
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
                form = SelectSurveyTaskForm(variables=variables, illness=illness)
                return render_to_response('consulting/consultation/monitoring/select_survey.html',
                                            {'form': form,
                                            'appointment': appointment,
                                            'templates': templates,
                                            'code_variables': settings.CUSTOM,
                                            'code_self_register': settings.SELF_REGISTER,
                                            'patient_user': appointment.patient,
                                            'appointment': appointment},
                                            context_instance=RequestContext(request))
            elif code_survey==str(settings.VIRTUAL_SURVEY):
                pass
            else:## HIDE DOCTOR's QUESTIONS
                questions_list = Question.objects.filter(questions_categories__categories_blocks__blocks_surveys=survey, questions_categories__categories_blocks__kind=kind).exclude(questions_categories__categories_blocks=exc_block)
                for question in questions_list:
                    task.questions.add(question)

            if 'cronos' in request.session and request.session['cronos']:
                return HttpResponseRedirect(reverse('cronos_tasks'))
            else:
                return HttpResponseRedirect(reverse('consulting_main',
                                        kwargs={'code_illness':code_illness,
                                                'id_appointment':id_appointment
                                               }))
            
    else:
        form = SelectSurveyTaskForm(variables=variables, illness=illness)

    return render_to_response(
            'consulting/consultation/monitoring/select_survey.html',
            {'form': form,
            'appointment': appointment,
            'templates': templates,
            'code_variables': settings.CUSTOM,
            'code_self_register': settings.SELF_REGISTER,
            'patient_user': appointment.patient,
            'illness': illness},
            context_instance=RequestContext(request))

@login_required
@only_doctor_consulting
def register_payment(request, id_appointment, code_illness):
    app = get_object_or_404(Appointment, pk=int(id_appointment))
    illness = get_object_or_404(Illness, code=code_illness)

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
            return HttpResponseRedirect(reverse('consulting_main',
                                        kwargs={'code_illness':code_illness,
                                                'id_appointment':id_appointment
                                               }))

    return render_to_response('consulting/consultation/monitoring/finish/register_payment.html', 
            {'form': form,
             'patient_user': app.patient,
             'appointment': app,
             'illness':illness},
        context_instance=RequestContext(request))

@login_required()
@only_doctor_consulting
def survey_kinds(request):
    if request.method == 'POST':
        code_survey = request.POST.get('code_survey', '')
        if code_survey == str(settings.CUSTOM):
            code_survey = settings.ANXIETY_DEPRESSION_SURVEY
        survey = get_object_or_404(Survey, code=code_survey)
        return HttpResponse(simplejson.dumps({'kinds':survey.get_available_kinds(flat=False)}))
    return Http404

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
        while Profile.objects.filter(user__username=username).count() > 0:
            code = str(randint(0, 9999))
            username = first_letter + second_letter + first_surname.lower() +\
                    code
    else:
        code = nif[LEN_NIF:]
        username = first_letter + second_letter + first_surname.lower() +\
                    code
    return username


def sendemail(user, password=None):
    subject = render_to_string('registration/identification_email_subject.txt',
                            {})
    # Email subject *must not* contain newlines
    subject = ''.join(subject.splitlines())

    message = render_to_string(
                            'registration/identification_email_message.txt',
                            {'username': user.username,
                            'password': password})

    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


@login_required()
@only_doctor_administrative
def newpatient(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor() or\
        logged_user_profile.is_administrative():
        same_username = False

        if request.method == "POST":
            if logged_user_profile.is_doctor():
                    exclude_list = ['user', 'role', 'doctor']
            else:
                exclude_list = ['user', 'role', 'doctor', 
                                'sex', 'status', 'profession']
            request_params = dict([k, v] for k, v in request.POST.items())
            request_params.update({'created_by': request.user.id})
            form = ProfileForm(request_params, exclude_list=exclude_list)
            if form.is_valid():
                username = generate_username(form)
                try:
                    Profile.objects.get(user__username=username)
                    same_username = True
                except Profile.DoesNotExist:
                    ############################USER###########################
                    password = pwd_generator()
                    user = User.objects.create_user(username=username,
                        password=password,
                        email=form.cleaned_data['email'])
                    user.first_name = format_string(form.cleaned_data['name'])
                    user.last_name = format_string(
                                        form.cleaned_data['first_surname'])\
                                        + ' ' +\
                                format_string(
                                        form.cleaned_data['second_surname'])
                    user.email = form.cleaned_data['email']
                    #user.save()
                    ##########################PROFILE##########################
                    try:
                        profile = form.save(commit=False)
                        if not profile.nif:
                            profile.nif = None
                        #Automatic to format name, first_surname and
                        #second_surname
                        if not profile.nif:
                            profile.nif = None
                        profile.name = format_string(form.cleaned_data['name'])
                        profile.first_surname = format_string(
                                        form.cleaned_data['first_surname'])
                        profile.second_surname = format_string(
                                        form.cleaned_data['second_surname'])

                        profile.role = settings.PATIENT
                        if not form.cleaned_data['postcode']:
                            profile.postcode = None
                        #Relationships between patient and doctor
                        if logged_user_profile.is_doctor():
                            profile.doctor = logged_user_profile.user
                        user.save()
                        profile.user = user
                        profile.save()
                        #default_illness = Illness.objects.get(
                        #                        id=settings.DEFAULT_ILLNESS)
                        #profile.illnesses.add(default_illness)
                        #profile.save()"""
                    except Exception:
                        #user.delete()
                        return HttpResponseRedirect(reverse('consulting_index'))
                    ###########################################################
                    #SEND EMAIL
                    if user.email:
                        sendemail(user, password)

                    return render_to_response(
                            'consulting/patient/patient_identification.html',
                            {'patient_user': user,
                            'newpatient': True},
                            context_instance=RequestContext(request))
        else:
            if logged_user_profile.is_doctor():
                exclude_list = ['user', 'role', 'doctor']
            else:
                exclude_list = ['user', 'role', 'doctor', 
                                'sex', 'status', 'profession']
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
                                Q(role__exact=settings.PATIENT) &
                                (Q(nif__istartswith=start)|
                                Q(name__icontains=start)|
                                Q(first_surname__icontains=start)|
                                Q(second_surname__icontains=start))).order_by(
                                'name', 'first_surname', 'second_surname')
            else:
                doctor_user = logged_user_profile.user
                profiles = Profile.objects.filter(
                                Q(doctor=doctor_user,
                                role__exact=settings.PATIENT) &
                                (Q(nif__istartswith=start)|
                                 Q(name__icontains=start)|
                                 Q(first_surname__icontains=start)|
                                 Q(second_surname__icontains=start)
                                )).order_by('name', 'first_surname', 'second_surname')
            data = {'ok': True,
                    'completed_names':
                    [{'id': profile.user.id,
                    'label': profile.get_full_name(),
                    'nif': profile.nif } for profile in profiles]
                    }
        return HttpResponse(simplejson.dumps(data))
    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@only_doctor_administrative
def editpatient_pm(request, patient_user_id):
    logged_user_profile = request.user.get_profile()
    
    if logged_user_profile.is_doctor():
        try:
            user = User.objects.get(id=patient_user_id, profiles__doctor=request.user)
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))
    elif logged_user_profile.is_administrative():
        try:
            user = User.objects.get(id=patient_user_id)
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

    profile = user.get_profile()
    doctor_form = DoctorSelectionForm(patient=profile)

    if request.method == "POST":
        redirect_to = request.POST.get('next', '')
        if logged_user_profile.is_doctor():
            exclude_list = ['user', 'role', 'doctor', 'illnesses']
        else:
            exclude_list = ['user', 'role', 'doctor',
                            'illnesses', 'sex', 'status', 'profession']

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
            email = form.cleaned_data['email']
            user.email = email

            if (name != name_form or\
                first_surname != first_surname_form or\
                nif != nif_form) or\
                (nif_form == '' and dob != dob_form):

                username = generate_username(form)
                profile.user.username = username
                profile.user.save()

                profile.save()

                #SEND EMAIL to warn new username
                if user.email:
                    sendemail(user)
                patient_user_id = user.id

                return HttpResponseRedirect(
                    '%s?next=%s' % (
                    reverse('consulting_patient_identification_pm',
                            args=[patient_user_id]),
                    redirect_to))
            else:
                profile.save()
                if redirect_to:
                    return HttpResponseRedirect(redirect_to)
                else:
                    return HttpResponseRedirect(reverse('consulting_index_pm'))
        else:
            return render_to_response(
                            'consulting/patient/patient.html',
                            {'form': form,
                            'doctor_form': doctor_form,
                            'edit': True,
                            'patient_user_id': patient_user_id,
                            'next': redirect_to},
                            context_instance=RequestContext(request))
    else:
        next = request.GET.get('next', '')
        if logged_user_profile.is_doctor():
            exclude_list = ['user', 'role', 'doctor', 'illnesses']
        else:
            exclude_list = ['user', 'role', 'doctor', 'illnesses', 
                            'sex', 'status', 'profession']

        if user.is_active:
            active = settings.ACTIVE
        else:
            active = settings.DEACTIVATE

        form = ProfileForm(instance=profile, exclude_list=exclude_list,
                            initial={'active': active})

    return render_to_response('consulting/patient/patient.html',
                            {'form': form,
                            'doctor_form': doctor_form,
                            'edit': True,
                            'patient_user_id': patient_user_id,
                            'next': next},
                            context_instance=RequestContext(request))



#METE EN SESIÓN EL PACIENTE
@login_required()
def pre_personal_data_pm(request, patient_user_id):
    logged_user_profile = request.user.get_profile()
    try:
        User.objects.get(id=patient_user_id)
    except User.DoesNotExist:
        return HttpResponseRedirect(reverse('consulting_index'))

    if logged_user_profile.is_doctor():
        request.session['patient_user_id'] = patient_user_id
        return HttpResponseRedirect(reverse('consulting_personal_data_pm', kwargs={'patient_user_id': patient_user_id}))
    elif logged_user_profile.is_administrative():
        return HttpResponseRedirect(reverse('consulting_editpatient_pm', kwargs={'patient_user_id': patient_user_id}))


    return HttpResponseRedirect(reverse('consulting_index'))

@login_required()
@never_cache
@only_doctor_consulting
def personal_data_pm(request, patient_user_id):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        try:
            #patient_user_id = request.session['patient_user_id']
            patient_user = User.objects.get(id=patient_user_id)
            if not patient_user.get_profile().doctor == request.user:
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
@only_doctor_consulting
def get_cie_tree(request, patient_user_id):
    logged_user_profile = request.user.get_profile()
    patient_user = get_object_or_404(User, id=patient_user_id)
    code_illness = request.GET.get('code', None)
    include = patient_user.get_profile().get_illness_set()
    if code_illness:
        illness = get_object_or_404(Illness, code=code_illness)
        action = request.GET.get('action', None)
        if not action:
            illness = [i.serialize() for i in Illness.objects.filter(parent__code=code_illness).order_by('code')]
        elif action == 'set':
            patient_user.get_profile().illnesses.add(illness)
            return HttpResponse(json.dumps({'data': _(u'Cambio realizado con éxito')}),
            status=200,
            mimetype='application/json')
        elif action == 'unset':
            patient_user.get_profile().illnesses.remove(illness)
            return HttpResponse(json.dumps({'data':  _(u'Cambio realizado con éxito')}),
            status=200,
            mimetype='application/json')
    else:   
        illness = [i.serialize(include) for i in Illness.objects.filter(parent__isnull=True).exclude(code=settings.DEFAULT_ILLNESS).order_by('id')]


    if request.is_ajax():
        return HttpResponse(json.dumps(illness),
                status=200,
                mimetype='application/json')
    else:
        return render_to_response(
                        'consulting/patient/cie_tree.html',
                        {'patient_user_id': patient_user.id,
                        'patient_user': patient_user,
                        'checked': json.dumps(['node_'+i.code for i in patient_user.get_profile().illnesses.all()]),
                        'data': json.dumps(illness)},
                        context_instance=RequestContext(request))



@login_required()
def patient_management(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_administrative():
        doctors = Profile.objects.filter(role=settings.DOCTOR)
        return render_to_response('consulting/pm/index_pm.html', {'doctors': doctors}, context_instance=RequestContext(request))
    elif logged_user_profile.is_doctor():
        form = ProfileFiltersForm()
        if request.method == "GET":
            form = ProfileFiltersForm(request.GET)
            query_filter = Q()
            exclude_filter = Q()
            for k, v in request.GET.items():
                if not v:
                    continue
                if k.startswith('date'):
                    day, month, year  = v.split('/')
                    if k.endswith('0'):
                        query_filter = query_filter & Q(created_at__gte=date(                                        int(year),
                                                                    int(month),
                                                                    int(day)))
                    else:
                        query_filter = query_filter & Q(created_at__lte=date(int(year),
                                                                    int(month),
                                                                    int(day)))
                elif k.startswith('age'):
                    if k.endswith('0'):
                        query_filter = query_filter & Q(dob__lte=datetime.now()-timedelta(days=int(v)*365.25))
                    else:
                         query_filter = query_filter & Q(dob__gte=datetime.now()-timedelta(days=int(v)*365.25))
                elif k.startswith('profession'):
                    query_filter = query_filter \
                        & Q(profession__in=request.GET.getlist(k))
                elif k.startswith('illnesses'):
                    query_filter = query_filter \
                        & Q(illnesses__code__in=request.GET.getlist(k))
                elif k.startswith('marital'):
                    query_filter = query_filter \
                        & Q(status__in=request.GET.getlist(k))
                elif k.startswith('sex'):
                    query_filter = query_filter \
                        & Q(sex__in=request.GET.getlist(k))
                elif k.startswith('education'):
                    query_filter = query_filter \
                        & Q(education__in=request.GET.getlist(k))
            if request.is_ajax():       
                return patient_list(request, request.user.id, query_filter)
        return render_to_response('consulting/pm/index_pm.html', {'form': form}, context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

@login_required()
@paginate(template_name='consulting/patient/list.html',
    list_name='patients', objects_per_page=settings.OBJECTS_PER_PAGE)
def patient_list(request, doctor_user_id, query_filter=None):
    patients = []
    if request.user.get_profile().is_administrative():
        if int(doctor_user_id) == request.user.id:
            patients = Profile.objects.filter(role=settings.PATIENT)
        else:
            patients = Profile.objects.filter(doctor__id=int(doctor_user_id),
                                              role=settings.PATIENT)
    elif request.user.get_profile().is_doctor() and request.user.id == int(doctor_user_id):
        patients = Profile.objects.filter(doctor__id=int(doctor_user_id),
                                          role=settings.PATIENT)

    if query_filter:
        patients = patients.filter(query_filter)

    queries_without_page = request.GET.copy()
    if queries_without_page.has_key('page'):
        del queries_without_page['page']
    
    template_data = {}
    template_data.update({'patients': patients, 
                          'queries':queries_without_page})
    return template_data

@login_required()
@paginate(template_name='consulting/patient/surveys/list.html',
    list_name='tasks', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_surveys(request):
    tasks = request.user.get_profile().get_pending_tasks()
    template_data = {}
    template_data.update({'tasks': tasks})
    return template_data

@login_required()
def searcher_profession(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor() or logged_user_profile.is_administrative():
        data = {'ok': False}

        if request.method == 'POST':
            start = request.POST.get("start", "").lower()

            professions = Profile.objects.filter(profession__istartswith=start).values_list('profession', flat=True).order_by('profession').distinct()

            data = {'ok': True,
                    'professions':list(professions)}
        return HttpResponse(json.dumps(data))
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
                Q(name__istartswith=start)).distinct()
            else:
                #settings.MEDICINE
                components = Component.objects.filter(
                Q(kind_component__exact=settings.MEDICINE),
                Q(name__istartswith=start)).distinct()

            data = {'ok': True,
                    'components':
                        [{'id': c.id, 'label': (c.name)} for c in components.order_by('name')]}
        return HttpResponse(json.dumps(data))
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
@never_cache
@paginate(template_name='consulting/patient/list_medicines.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def get_medicines(request, filter_option, id_patient):
    logged_user_profile = request.user.get_profile()

    if id_patient:
        patient_user = User.objects.get(pk=int(id_patient))
        if 'appointment_id' in request.session:
            appointment = Appointment.objects.get(pk=request.session['appointment_id'])
        else:
            appointment = None
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
                            'appointment': appointment,
                            'template_name': template_name,
                            'csrf_token': get_token(request)})
    return template_data

@login_required()
@only_doctor_consulting
def list_medicines(request, id_appointment=None, code_illness=None):
    logged_user_profile = request.user.get_profile()

    if id_appointment and code_illness:
        appointment = Appointment.objects.get(pk=int(id_appointment))
        request.session['appointment_id'] = appointment.id
        patient_user = appointment.patient
        illness = Illness.objects.get(code=code_illness)
    else:
        patient_user_id = request.session['patient_user_id']
        patient_user = User.objects.get(id=patient_user_id)
        appointment = None
        illness = None


    return render_to_response('consulting/patient/list_medicines.html', 
                            {'patient_user': patient_user,
                            'patient_user_id':patient_user.id,
                            'appointment':appointment,
                            'illness': illness,
                            'csrf_token': get_token(request)
                            },
                    context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def list_appointments(request, patient_user_id):
    logged_user_profile = request.user.get_profile()
    
    #patient_user_id = request.session['patient_user_id']

    patient_user = User.objects.get(id=patient_user_id)

    return render_to_response('consulting/patient/list_appointments.html',
            {'patient_user': patient_user,
             'patient_user_id': patient_user_id,
             'csrf_token': get_token(request)}, 
             context_instance=RequestContext(request))

@login_required()
@only_doctor_consulting
@paginate(template_name='consulting/patient/appointments.html',
    list_name='events', objects_per_page=settings.OBJECTS_PER_PAGE)
def get_appointments(request, patient_user_id, filter_option = None):
    logged_user_profile = request.user.get_profile()

    queries_without_page = request.GET.copy()
    if queries_without_page.has_key('page'):
        del queries_without_page['page']

    #patient_user_id = request.session['patient_user_id']
    patient_user = User.objects.get(id=patient_user_id)
    appointments = Appointment.objects.filter(patient=patient_user).order_by('-date')
    
    if filter_option != 'all':
        virtual = False
        if filter_option == 'virtual':
            virtual = True
        appointments = appointments.exclude(notify=virtual)

    if request.method == "GET":
        subfilter_option = request.GET.get('filter', '')
        if subfilter_option.isdigit():
            appointments = appointments.filter(status=int(subfilter_option))


    template_data = {}
    template_data.update({'patient_user': patient_user,
                            'events': appointments,
                            'queries': queries_without_page,
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
    return report(request, id_task)

def report(request, id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    patient = task.patient.get_profile()
    marks = task.get_variables_mark()
    beck_mark = task.calculate_beck_mark()
    hamilton_mark, hamilton_submarks = task.calculate_hamilton_mark()
    dimensions = task.get_dimensions_mark()
    ave_mark = task.calculate_mark_by_code('AVE')
    light_mark = task.calculate_mark_by_code('L')
    blaxter_mark = task.calculate_mark_by_code('AS')
    prev_meds = Medicine.objects.filter(patient=task.patient, is_previous=True).order_by('-date')
    medicines = Medicine.objects.none()
    if task.appointment:
        medicines = Medicine.objects.filter(patient=task.patient,
                                            appointment=task.appointment,
                                            is_previous=False
                                            ).order_by('-date')

    try:
        recurrent = beck_mark > 13 and task.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(code__in=['AP4','AP5','AP6'])
        recurrent = recurrent or (hamilton_mark > 18 and task.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(code__in=['AP1','AP3']))
    except:
        recurrent = None
    try:
        h6 = hamilton_submarks['H6']
    except:
        h6 = None

    try:
        conclusions = Conclusion.objects.filter(appointment=task.appointment)
    except: 
        conclusions = Conclusion.objects.none()

    values = {}
    if task.treated_blocks.filter(is_scored=True).exists():
        tasks = Task.objects.filter(patient=task.patient,survey=task.survey, completed=True).order_by('-end_date')[:5]
       
        mindate = tasks[0].end_date
        maxdate = tasks[0].end_date
        for t in tasks:
            mindate = t.end_date < mindate and t.end_date or mindate
            maxdate = t.end_date > maxdate and t.end_date or maxdate
            variables = t.get_variables_mark()
            for var, mark in variables.items():
                if var in values:
                    values[var].insert(0,(t, mark))
                else:
                    values[var] =[(t, mark),]
    data = {'task': task,
            'marks': marks,
            'patient': patient,
            'conclusions':conclusions,
            'beck_mark':beck_mark,
            'beck_scale':task.calculate_scale(Scale.objects.get(key='depression')),
            'hamilton_mark':hamilton_mark,
            'hamilton_scale': task.calculate_scale(Scale.objects.get(key='anxiety')),
            'dimensions': dimensions,
            'values': values,
            'h6_mark': h6,
            'ave_mark':ave_mark,
            'ave_status':task.calculate_scale(Scale.objects.get(key='stress')),
            'recurrent':recurrent,
            'light_mark':light_mark,
            'blaxter_mark':blaxter_mark,
            'as_mark':task.calculate_mark_by_code('AS'),
            'treatment':medicines,
            'prev_treatment':prev_meds,
            'logo': os.path.join(settings.STATICFILES_DIRS[0], 'img', 'logo_report.JPG')
            }

    if request.GET and request.GET.get('as', '') == 'pdf':
        mypdf = PDFTemplateView()
        mypdf.request=request
        mypdf.filename ='Consulting30_report.pdf'
        if 'cronos' in request.session and request.session['cronos']:
            mypdf.filename ='Cronos_report.pdf'
        mypdf.header_template = 'ui/includes/pdf_header.html'
        mypdf.template_name='consulting/consultation/report/base.html'
        data.update({'as_pdf':True})
        return mypdf.render_to_response(context=data)
    else:
        return render_to_response('consulting/consultation/report/base.html',
                                data,
                                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
@paginate(template_name='consulting/patient/list_reports.html',
    list_name='reports', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_reports(request, patient_user_id):
    logged_user_profile = request.user.get_profile()

    #patient_user_id = request.session['patient_user_id']

    if logged_user_profile.is_doctor():
        patient_user = User.objects.get(id=patient_user_id)

        reports = Task.objects.filter(Q(patient=patient_user), 
                Q(completed=True) | Q(survey__code=settings.SELF_REGISTER)
                ).order_by('-updated_at')

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
@only_doctor_consulting
def list_provisional_reports(request, id_appointment, code_illness):
    logged_user_profile = request.user.get_profile()

    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    illness = get_object_or_404(Illness, code=code_illness)

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
@only_doctor_consulting
@paginate(template_name='consulting/patient/list_messages.html',
    list_name='messages', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_messages(request, patient_user_id):
    logged_user_profile = request.user.get_profile()

    #patient_user_id = request.session['patient_user_id']

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
@only_doctor_consulting
@paginate(template_name='consulting/patient/list_recommendations.html',
    list_name='conclusions', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_recommendations(request, patient_user_id):
    logged_user_profile = request.user.get_profile()

    #patient_user_id = request.session['patient_user_id']

    if logged_user_profile.is_doctor():
        patient_user = User.objects.get(id=patient_user_id)

        recommendations = Conclusion.objects.filter(appointment__patient=patient_user).exclude(recommendation__iexact="").order_by('-date')

        template_data = {}
        template_data.update({'patient_user': patient_user,
                                'conclusions': recommendations,
                                'patient_user_id': patient_user_id,
                                'csrf_token': get_token(request)})
        return template_data
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

@login_required()
@only_doctor_consulting
def user_evolution(request, patient_user_id, block_code, return_xls=False):
    logged_user_profile = request.user.get_profile()
    blocks = Block.objects.filter(code=block_code)
    if blocks:
        block = blocks[0]
    else:
        raise Http404

    #patient_user_id = request.session['patient_user_id']
    limit = 5
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

    tasks = Task.objects.filter(Q(patient=patient_user,treated_blocks__code=block_code, completed=True),date_filter).order_by('-end_date').distinct()[:limit]

    latest_marks, latest_dimensions = {}, {}
    scales, yscales = {}, {}

    vmax, vmin = 0, 0

    vticks = []
    end_dates = set()

    for t in tasks:
        #res =t.task_results.values('block').annotate(Max('id'))
        marks = t.get_variables_mark()
        dimensions = t.get_dimensions_mark(marks)
        for d, value in dimensions.items():
            if not d.name:
                pass
            elif d in latest_dimensions:
                latest_dimensions[d].insert(0,[t, value])
            else:
                latest_dimensions[d] = [[t, value]]
        for var, mark in marks.items():
            vmax = max(vmax, var.vmax)
            vmin = min(vmin, var.vmin)
            if mark != None:
                if var in latest_marks.keys():
                    latest_marks[var].insert(0, [t, mark])
                else:
                    latest_marks[var] = [[t, mark]]
            if not t.end_date in vticks:
                vticks.append(t.end_date)
        
        for scale in t.get_scales():
            end_dates.add(t)

            if scale['name'] in scales:
                scales[scale['name']].insert(0, [t, scale['mark']])
            else:
                scales[scale['name']] = [[t, scale['mark']]]
                yscales[scale['name']] = scale['scale'].levels


    # Fix empty slots
    for task in end_dates:
        for k, v in scales.items():
            next = False
            for i in range(len(v)):
                if v[i][0].end_date == task.end_date:
                    next = True
                    break
                elif v[i][0].end_date > task.end_date:
                    scales[k].insert(i, [t, ''])
                    next = True
                    break
                elif len(v) == i+1:
                    scales[k].insert(i+1, [task, ''])
            if next:
                continue



    vticks.sort()

    if request.GET.get('as', '') == 'xls':
        sheets = [('Variables', latest_marks)]
        if latest_dimensions:
            sheets.append(('Dimensiones', latest_dimensions))
        if scales:
            sheets.append(('Escalas', scales))
        style_head = xlwt.easyxf('font: name Times New Roman, color-index black, bold on')
        style_value = xlwt.easyxf('font: name Times New Roman, color-index blue', num_format_str='#,##0.00')
        style_date = xlwt.easyxf(num_format_str='DD-MM-YYYY')

        wb = xlwt.Workbook(encoding='utf-8')
        for s, d in sheets:
            ws = wb.add_sheet(s)
            r, c = 1, 0
            for var, lst in d.items():
                if hasattr(var, 'name'):
                    ws.write(r, c , var.name, style_head)
                else:
                    ws.write(r, c , var, style_head)
                for task, val in lst: 
                    c += 1
                    ws.write(r, c, val, style_value)
                    if r == 1:
                        ws.write(0, c, task.end_date, style_date)
                c = 0
                r += 1
        tmp_io = cStringIO.StringIO()
        wb.save(tmp_io)
        response = HttpResponse(tmp_io.getvalue(), content_type='application/vnd.ms-excel')
        tmp_io.close()
        response['Content-Disposition'] = 'attachment; filename="Consulting30_%s.xls"'% block.name.encode('ascii', 'ignore').replace(' ','_')
        return response


    return render_to_response('consulting/patient/user_evolution.html', 
                                {'patient_user': patient_user,
                                 'patient_user_id': patient_user_id,
                                 'form': form,
                                 'latest_marks': latest_marks,
                                 'latest_dimensions': latest_dimensions,
                                 'scales': scales,
                                 'vmax': vmax, 
                                 'vmin': vmin,
                                 'yscales': yscales,
                                 'active_tab': (request.POST.get('active_tab','')).replace('#',''),
                                 'ticks_variables': vticks,
                                 'survey_block': block},
                            context_instance=RequestContext(request))

@login_required()
@only_doctor_consulting
def save_notes(request):
    if request.POST and request.POST.get('name','')=='notes':
        request.session["notes"] = request.POST.get('value')
        return HttpResponse('')
    return HttpResponse('Error')

@login_required()
@only_doctor_consulting
def dismiss_alert(request):
    id_alert = request.GET.get('id','')
    if id_alert:
        alert = get_object_or_404(Alert, id=int(id_alert))
        alert.revised_date=datetime.today()
        alert.save()
    return HttpResponse('')

@login_required()
def get_user_guide(request):
    import os
    profile = request.user.get_profile()
    if profile.is_doctor():
        filename = 'doctor_guide.pdf'
    elif profile.is_administrative():
        filename = 'administrative_guide.pdf'
    elif profile.is_patient():
        filename = 'patient_guide.pdf'
    else:
        raise Http404
    for folder in settings.STATICFILES_DIRS:
        abspath = os.path.join(folder, 'pdf', filename)
        if os.path.exists(abspath):
            pdf = open(abspath,'r')
            response = HttpResponse(content=pdf.read())
            response['Content-Type']= 'application/pdf'
            response['Content-Disposition'] = 'attachment; filename=%s' \
                                            % _(u'Consulting_user_guide.pdf')
            return response
    
    raise Http404

def pwd_generator():
    return ''.join(random.choice(string.ascii_uppercase + string.digits + string.ascii_lowercase) for x in range(settings.PASSWORD_MIN_LENGTH))


def error_page(request):
    return render_to_response('500.html',
                                {},
                                context_instance=RequestContext(request))

