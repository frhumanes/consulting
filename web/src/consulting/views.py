# -*- encoding: utf-8 -*-
import time
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
from consulting.models import Medicine, Task, Conclusion, Result
from cal.models import Appointment, Slot, SlotType
from illness.models import Illness
from survey.models import Survey, Block, Question, Option
from formula.models import Variable, Formula, Dimension

from userprofile.forms import ProfileForm, ProfileSurveyForm
from consulting.forms import MedicineForm
from consulting.forms import  ConclusionForm
from consulting.forms import  ActionSelectionForm
from consulting.forms import SelectTaskForm
from consulting.forms import SelectOtherTaskForm
from consulting.forms import SelectNotAssessedVariablesForm
from consulting.forms import SymptomsWorseningForm
from illness.forms import IllnessSelectionForm, IllnessAddPatientForm
from survey.forms import SelectBlockForm
from survey.forms import QuestionsForm
from survey.forms import SelectBehaviorSurveyForm
from cal.forms import AppointmentForm

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
        return render_to_response('consulting/patient/index_patient.html', {},
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
                    patient=patient, id_result=id_result)
    if id_result:
        data.update({'id_result': id_result})

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
                        (code == settings.ANXIETY_DEPRESSION_EXTENSIVE) or\
                        (code == settings.ANXIETY_DEPRESSION_SHORT):
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
    if request.method == 'POST':
        form = IllnessSelectionForm(request.POST,
                                    id_appointment=appointment.id)
        if form.is_valid():
            code_illness = form.cleaned_data['illness']
            if code_illness == str(settings.DEFAULT_ILLNESS):
                return HttpResponseRedirect(reverse('consulting_select_action',
                                            args=[id_appointment]))
            elif code_illness == str(settings.ANXIETY_DEPRESSION):
                ia_survey = get_object_or_404(Survey,
                                            code=settings.INITIAL_ASSESSMENT)
                tasks_with_ia_survey = Task.objects.filter(
                                                patient=appointment.patient,
                                                survey=ia_survey)
                if tasks_with_ia_survey:
                    #HAY VALORACIÓN INICIAL
                    last_task_with_ia_survey = tasks_with_ia_survey.latest(
                                                            'creation_date')
                    if not last_task_with_ia_survey.completed:
                        #VALORACIÓN INICIAL NO COMPLETADA
                        return HttpResponseRedirect(
                                reverse('consulting_administrative_data',
                                        args=[last_task_with_ia_survey.id,
                                                id_appointment]))
                    else:
                        #VALORACIÓN INICIAL COMPLETADA LUEGO AHORA SEGUIMIENTO'
                        return HttpResponseRedirect(
                        reverse('consulting_monitoring', args=[id_appointment]))
                else:
                    #NO HAY VALORACIÓN INICIAL
                    task = Task(created_by=request.user,
                        patient=appointment.patient, survey=ia_survey,
                        appointment=appointment, self_administered=False)
                    task.save()

                    return HttpResponseRedirect(
                                reverse('consulting_administrative_data',
                                        args=[task.id, id_appointment]))

            else:
                return HttpResponseRedirect(reverse('consulting_index'))
    else:
        form = IllnessSelectionForm(id_appointment=appointment.id)
    return render_to_response('consulting/consultation/illness/select.html',
                                {'form': form,
                                'patient_user': appointment.patient,
                                'id_appointment': id_appointment},
                                context_instance=RequestContext(request))


def task_completed(id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    result = task.task_results.latest('date')

    if task.treated_blocks.count() == task.survey.num_blocks:
        options_result = result.options.all()
        questions = task.questions.all()
        if questions:
            for question in questions:
                options = question.question_options.all().order_by('id')
                enc_option = False
                for option in options:
                    if option in options_result:
                        enc_option = True
                        break
                if not enc_option:
                    return False
            return True
        else:
            blocks = result.task.treated_blocks.all().order_by('code')

            for block in blocks:
                categories = block.categories.all().order_by('code')
                for category in categories:
                    questions = category.questions.all().order_by('id')
                    for question in questions:
                        options = question.question_options.all().order_by('id')
                        enc_option = False
                        for option in options:
                            if option  in options_result:
                                enc_option = True
                                break
                        if not enc_option:
                            return False
            return True
    else:
        return False

def check_task_completion(id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    answers = task.get_answers()
    if not answers:
        return False
    questions = task.questions.filter(required=True)
    if task.treated_blocks.count() < task.survey.num_blocks:
        return False
    if not questions:
        questions = Question.objects.filter(required=True,kind__in=(0, task.patient.get_profile().sex),
                                            questions_categories__categories_blocks__blocks_tasks=task)
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
        form = ConclusionForm()

    return render_to_response('consulting/consultation/conclusion/conclusion.html',
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
                'consulting/consultation/conclusion/new_medicine_conclusion.html',
                {'form': form,
                'id_conclusion': id_conclusion,
                'patient_user': patient},
                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
@paginate(
    template_name='consulting/consultation/conclusion/list_medicines_conclusion.html',
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
    template_name='consulting/consultation/conclusion/list_medicines_conclusion.html',
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
                        'consulting/consultation/conclusion/detail_medicine.html',
                        {'medicine': medicine,
                        'id_conclusion': conclusion.id},
                        context_instance=RequestContext(request))
        except Medicine.DoesNotExist:
                return HttpResponseRedirect(reverse('consulting_index'))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@only_doctor_consulting
@paginate(template_name='consulting/consultation/conclusion/list_medicines_ajax_conclusion.html',
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
            code == settings.ANXIETY_DEPRESSION_EXTENSIVE or\
            code == settings.ANXIETY_DEPRESSION_SHORT):
        return HttpResponseRedirect(reverse('consulting_index'))

    variables = get_variables(result.id, settings.DEFAULT_NUM_VARIABLES)

    if request.method == 'POST':
        form = SelectTaskForm(request.POST, variables=variables)
        if form.is_valid():

            code_survey = form.cleaned_data['survey']
            from_date = form.cleaned_data['from_date']
            to_date = form.cleaned_data['to_date']

            if code_survey == str(settings.ANXIETY_DEPRESSION_EXTENSIVE) or\
                code_survey == str(settings.ANXIETY_DEPRESSION_SHORT):
                survey = get_object_or_404(Survey, code=int(code_survey))
            else:
                treated_blocks = result.task.treated_blocks.all()
                ade_block = get_object_or_404(Block,
                                    code=settings.ANXIETY_DEPRESSION_EXTENSIVE)
                ads_block = get_object_or_404(Block,
                                    code=settings.ANXIETY_DEPRESSION_SHORT)
                if ade_block in treated_blocks:
                    kind = settings.EXTENSO
                    survey = get_object_or_404(Survey,
                                    code=settings.ANXIETY_DEPRESSION_EXTENSIVE)
                elif ads_block in treated_blocks:
                    kind = settings.ABREVIADO
                    survey = get_object_or_404(Survey,
                                    code=settings.ANXIETY_DEPRESSION_SHORT)
                else:
                    return HttpResponseRedirect(reverse('consulting_index'))

            task = Task(created_by=request.user, patient=appointment.patient,
            appointment=appointment, self_administered=True, survey=survey,
            from_date=from_date, to_date=to_date)
            task.save()

            id_variables = form.cleaned_data['variables']
            if id_variables:
                variables = Variable.objects.filter(id__in=id_variables)
                for variable in variables:
                    formulas = variable.variable_formulas.filter(kind=kind)
                    for formula in formulas:
                        codes = formula.polynomial.split('+')
                        for code in codes:
                            question = get_object_or_404(Question, code=code)
                            task.questions.add(question)

            return HttpResponseRedirect(reverse('consulting_index'))
    else:
        form = SelectTaskForm(variables=variables)

    return render_to_response(
                'consulting/consultation/select_self_administered_survey.html',
                {'form': form,
                'id_appointment': id_appointment,
                'id_result': result.id,
                'code_variables': settings.VARIABLES,
                'patient_user': appointment.patient},
                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def check_conclusion(request, id_conclusion):
    conclusion = get_object_or_404(Conclusion, pk=int(id_conclusion))
    result = conclusion.result
    year = time.localtime()[0]
    if result:
        id_task = result.task.id
        code = result.survey.code

        if (code == settings.INITIAL_ASSESSMENT or\
            code == settings.ANXIETY_DEPRESSION_EXTENSIVE or\
            code == settings.ANXIETY_DEPRESSION_SHORT) and\
            check_task_completion(id_task):
            return HttpResponseRedirect(
                                    reverse('consulting_select_other_survey',
                                    args=[conclusion.appointment.id, result.id]))
        else:
            return HttpResponseRedirect(reverse('consulting_select_year_month',
                                args=[conclusion.patient.id, year, result.id]))

    return HttpResponseRedirect(reverse('consulting_select_year_month',
                                    args=[conclusion.patient.id, year]))


@login_required()
@only_doctor_consulting
def select_other_survey(request, id_appointment, id_result):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    result = get_object_or_404(Result, pk=int(id_result))
    code = result.survey.code
    kind = result.survey.kind

    if not (code == settings.INITIAL_ASSESSMENT or\
            code == settings.ANXIETY_DEPRESSION_EXTENSIVE or\
            code == settings.ANXIETY_DEPRESSION_SHORT):

        return HttpResponseRedirect(reverse('consulting_index'))

    variables = get_variables(id_result, settings.DEFAULT_NUM_VARIABLES)

    if request.method == 'POST':
        form = SelectOtherTaskForm(request.POST, variables=variables)
        if form.is_valid():
            code_survey = form.cleaned_data['survey']

            if code_survey == str(settings.ANXIETY_DEPRESSION_EXTENSIVE) or\
                code_survey == str(settings.ANXIETY_DEPRESSION_SHORT):
                survey = get_object_or_404(Survey, code=int(code_survey))
            else:
                treated_blocks = result.task.treated_blocks.all()
                ade_block = get_object_or_404(Block,
                                    code=settings.ANXIETY_DEPRESSION_EXTENSIVE)
                ads_block = get_object_or_404(Block,
                                    code=settings.ANXIETY_DEPRESSION_SHORT)
                if ade_block in treated_blocks:
                    kind = settings.EXTENSO
                    survey = get_object_or_404(Survey,
                                    code=settings.ANXIETY_DEPRESSION_EXTENSIVE)
                elif ads_block in treated_blocks:
                    kind = settings.ABREVIADO
                    survey = get_object_or_404(Survey,
                                    code=settings.ANXIETY_DEPRESSION_SHORT)
                else:
                    return HttpResponseRedirect(reverse('consulting_index'))

            task = Task(created_by=request.user, patient=appointment.patient,
            appointment=appointment, self_administered=False, survey=survey)
            task.save()

            id_variables = form.cleaned_data['variables']
            if id_variables:
                variables = Variable.objects.filter(id__in=id_variables)
                for variable in variables:
                    formulas = variable.variable_formulas.filter(kind=kind)
                    for formula in formulas:
                        codes = formula.polynomial.split('+')
                        for code in codes:
                            question = get_object_or_404(Question, code=code)
                            task.questions.add(question)

            return HttpResponseRedirect(reverse('consulting_other_block',
                                                args=[task.id, id_appointment]))
    else:
        form = SelectOtherTaskForm(variables=variables)

    year = time.localtime()[0]
    destination = '/consultation/new_app/select_year_month/' +\
                    str(appointment.patient.id) + '/' + str(year) + '/' +\
                    str(id_result)
    return render_to_response(
                        'consulting/consultation/select_other_survey.html',
                        {'form': form,
                        'id_appointment': id_appointment,
                        'id_result': id_result,
                        'destination': destination,
                        'code_variables': settings.VARIABLES,
                        'patient_user': appointment.patient},
                        context_instance=RequestContext(request))


def get_variables(id_result, num=None):
    marks = get_variables_mark(id_result)
    variables = []
    if num != None:
        values = marks.values()
        values.sort()
        n_mark = values[-num]
    else:
        n_mark = 0
    for var, mark in marks.items():
        if mark >= n_mark:
            variables.append((var.id, var.name))
    return variables


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
    result.options.add(sex_option)
    result.options.add(status_option)
    result.save()

    return result


@login_required()
@only_doctor_consulting
def administrative_data(request, id_task, id_appointment):
    task = get_object_or_404(Task, pk=int(id_task))
    user = task.patient
    profile = user.get_profile()
    my_block = get_object_or_404(Block, code=int(settings.ADMINISTRATIVE_DATA))
    code_block = settings.PRECEDENT_RISK_FACTOR

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

                if my_block not in treated_blocks:
                    task.treated_blocks.add(my_block)

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

                if my_block not in treated_blocks:
                    task.treated_blocks.add(my_block)

                if check_task_completion(task.id):
                    task.completed = True
                    task.end_date = datetime.now()
                    task.save()

                return HttpResponseRedirect(
                    reverse('consulting_block', args=[result.id, code_block]))
        else:
            return render_to_response(
                            'consulting/consultation/administrative_data.html',
                            {'form': form,
                            'patient_user': user,
                            'task': task,
                            'id_appointment': id_appointment,
                            'my_block': my_block},
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
                            'my_block': my_block},
                            context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def block(request, id_result, code_block):
    result = get_object_or_404(Result, pk=int(id_result))
    block = get_object_or_404(Block, pk=int(code_block))
    treated_blocks = result.task.treated_blocks.all()
    dic = {}
    categories = block.categories.all().order_by('id')
    for category in categories:
        questions = category.questions.filter(kind__in=[settings.UNISEX, result.patient.get_profile().sex]).order_by('id')
        for question in questions:
            options = question.question_options.all().order_by('id')
            dic[question.id] = [
                            (option.id, option.text)for option in options]
    if request.method == 'POST':
        form = QuestionsForm(request.POST, dic=dic, selected_options=[])
        if form.is_valid():
            new_result = Result(patient=result.patient, 
                            survey=result.survey, 
                            task=result.task,
                            block=block,
                            created_by=result.created_by, 
                            appointment=result.appointment)
            new_result.save()
            items = form.cleaned_data.items()
            for name_field, values in items:
                if isinstance(values, list):
                    for value in values:
                        option = Option.objects.get(pk=int(value))
                        new_result.options.add(option)
                        #new_result.save()
                elif values:
                    option = Option.objects.get(pk=int(values))
                    new_result.options.add(option)


            if block not in treated_blocks:
                result.task.treated_blocks.add(block)

            if check_task_completion(result.task.id):
                result.task.completed = True
                result.task.end_date = datetime.now()
                result.task.save()

            if code_block == str(settings.PRECEDENT_RISK_FACTOR):
                return HttpResponseRedirect(
                            reverse('consulting_new_medicine_survey',
                                    args=[result.id]))
            elif code_block == str(settings.ANXIETY_DEPRESSION_EXTENSIVE) or\
                code_block == str(settings.ANXIETY_DEPRESSION_SHORT):
                return HttpResponseRedirect(reverse('consulting_conclusion',
                                args=[result.task.appointment.id, result.id]))
            else:
                return HttpResponseRedirect(reverse('consulting_index'))
    else:
        task = result.task
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
                            'result': result,
                            'my_block': block,
                            'patient_user': result.patient},
                            context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def other_block(request, id_task, id_appointment):
    task = get_object_or_404(Task, pk=int(id_task))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))

    if task.task_results.all():
        last_result = task.task_results.latest('date')

        if last_result:
            selected_options = last_result.options.all()
    else:
        selected_options = []

    dic = {}
    treated_blocks = task.treated_blocks.all()
    blocks = task.survey.blocks.all()
    if blocks:
        block = task.survey.blocks.all()[0]
    else:
        return HttpResponseRedirect(reverse('consulting_index'))
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
        form = QuestionsForm(request.POST, dic=dic, selected_options=[])

        if form.is_valid():
            result = Result(patient=task.patient, survey=task.survey, task=task,
                    created_by=request.user, appointment=appointment)
            result.save()

            if task.task_results.count() == 1:
                task.start_date = result.date
                task.save()

            items = form.cleaned_data.items()
            for name_field, values in items:
                if values_list:
                    if isinstance(values, list):
                        for value in values:
                            option = Option.objects.get(pk=int(value))
                            result.options.add(option)
                            #new_result.save()
                    elif values:
                        option = Option.objects.get(pk=int(values))
                        result.options.add(option)

            if block not in treated_blocks:
                task.treated_blocks.add(block)

            if check_task_completion(task.id):
                task.completed = True
                task.end_date = datetime.now()
                task.save()

            return HttpResponseRedirect(reverse('consulting_conclusion',
                                        args=[task.appointment.id, result.id]))
    else:
        form = QuestionsForm(dic=dic, selected_options=selected_options)

    return render_to_response('consulting/consultation/other_block.html',
                            {'form': form,
                            'task': task,
                            'id_appointment': id_appointment,
                            'my_block': block,
                            'patient_user': task.patient},
                            context_instance=RequestContext(request))


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
            result = Result(patient=task.patient, survey=task.survey, task=task,
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
                        result.options.add(option)
                elif values:
                    option = Option.objects.get(pk=int(values))
                    result.options.add(option)

            if block not in treated_blocks:
                task.treated_blocks.add(block)

            if check_task_completion(task.id):
                task.completed = True
                task.end_date = datetime.now()
                task.save()

            return HttpResponseRedirect(
                    reverse('consulting_symptoms_worsening', args=[result.id]))
    else:
        form = QuestionsForm(dic=dic, selected_options=selected_options)

    return render_to_response('consulting/patient/surveys/block.html',
                            {'form': form,
                            'task': task},
                            context_instance=RequestContext(request))


@login_required()
@only_patient_consulting
def symptoms_worsening(request, id_result):
    result = get_object_or_404(Result, pk=int(id_result))
    if request.method == 'POST':
        form = SymptomsWorseningForm(request.POST)
        if form.is_valid():
            symptoms_worsening = form.cleaned_data['symptoms_worsening']
            result.symptoms_worsening = symptoms_worsening
            result.save()
            return HttpResponseRedirect(reverse('consulting_list_surveys'))
    else:
        form = SymptomsWorseningForm()
    return render_to_response('consulting/patient/surveys/symptoms_worsening.html',
                                {'form': form,
                                'id_result': result.id},
                                context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def select_block(request, id_result):
    result = get_object_or_404(Result, pk=int(id_result))
    if request.method == 'POST':
        form = SelectBlockForm(request.POST)
        if form.is_valid():
            code_block = form.cleaned_data['block']
            return HttpResponseRedirect(reverse('consulting_block',
                                            args=[id_result, code_block]))
    else:
        form = SelectBlockForm()
    return render_to_response('consulting/consultation/select_block.html',
                                {'form': form,
                                'patient_user': result.patient,
                                'result': result},
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

    if result.survey.code == settings.PREVIOUS_STUDY:
        destination = '/consultation/conclusion/' +\
                        str(result.task.appointment.id) + '/' + str(result.id)
    elif result.survey.code == settings.INITIAL_ASSESSMENT:
        treated_blocks = result.task.treated_blocks.all()
        if treated_blocks.filter(code=settings.ANXIETY_DEPRESSION_EXTENSIVE):
            destination = '/consultation/survey/block/' +\
            str(result.id) + '/' +\
            str(settings.ANXIETY_DEPRESSION_EXTENSIVE)
        elif treated_blocks.filter(
                            code=settings.ANXIETY_DEPRESSION_SHORT):
            destination = '/consultation/survey/block/' +\
            str(result.id) + '/' +\
            str(settings.ANXIETY_DEPRESSION_SHORT)
        else:
            destination = '/consultation/survey/select_block/' + str(result.id)

    block = get_object_or_404(Block, code=settings.PRECEDENT_RISK_FACTOR)
    return render_to_response(
                'consulting/consultation/new_medicine_survey.html',
                {'form': form,
                'id_appointment': result.task.appointment.id,
                'id_result': id_result,
                'name_survey': result.survey.name,
                'code_block': settings.PRECEDENT_RISK_FACTOR,
                'name_block': block.name,
                'patient_user': patient,
                'destination': destination},
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

    block = get_object_or_404(Block, code=settings.PRECEDENT_RISK_FACTOR)

    if result.survey.code == settings.PREVIOUS_STUDY:
        destination = '/consultation/conclusion/' +\
                        str(result.task.appointment.id) + '/' + str(result.id)
    elif result.survey.code == settings.INITIAL_ASSESSMENT:
        treated_blocks = result.task.treated_blocks.all()
        if treated_blocks.filter(code=settings.ANXIETY_DEPRESSION_EXTENSIVE):
            destination = '/consultation/survey/block/' +\
            str(result.id) + '/' +\
            str(settings.ANXIETY_DEPRESSION_EXTENSIVE)
        elif treated_blocks.filter(
                            code=settings.ANXIETY_DEPRESSION_SHORT):
            destination = '/consultation/survey/block/' +\
            str(result.id) + '/' +\
            str(settings.ANXIETY_DEPRESSION_SHORT)
        else:
            destination = '/consultation/survey/select_block/' + str(result.id)

    template_data = {}
    template_data.update({'patient_user': result.patient,
                        'medicines': medicines,
                        'id_appointment': result.task.appointment.id,
                        'id_result': id_result,
                        'name_survey': result.survey.name,
                        'code_block': block.code,
                        'name_block': block.name,
                        'destination': destination,
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
                        'consulting/consultation/conclusion/detail_medicine.html',
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


################################## MONITORING #################################
@login_required()
@only_doctor_consulting
def monitoring(request, id_appointment):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    return render_to_response(
                'consulting/consultation/monitoring/index.html',
                {'patient_user': appointment.patient,
                'appointment': appointment},
                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
@paginate(
    template_name='consulting/consultation/monitoring/incomplete_surveys/list.html',
    list_name='tasks', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_incomplete_surveys(request, id_appointment):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    patient = appointment.patient
    tasks = Task.objects.filter(
    Q(patient=patient, completed=False, self_administered=False,
        assess=True) |
    Q(patient=patient, completed=False, self_administered=True,
        assess=True, to_date__lt=datetime.now())).order_by('-creation_date')

    template_data = {}
    template_data.update({'patient_user': patient,
                        'tasks': tasks,
                        'appointment': appointment,
                        'csrf_token': get_token(request)})
    return template_data


@login_required()
@only_doctor_consulting
def not_assess_task(request, id_task, id_appointment):
    task = get_object_or_404(Task, pk=int(id_task))
    task.assess = False
    task.end_date = datetime.now()
    task.save()

    return HttpResponseRedirect(reverse('consulting_list_incomplete_surveys',
                                        args=[id_appointment]))


@login_required()
@only_doctor_consulting
def incomplete_block(request, id_task, id_appointment):
    task = get_object_or_404(Task, pk=int(id_task))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))

    if task.task_results.all():
        last_result = task.task_results.latest('date')

        if last_result:
            selected_options = last_result.options.all()
    else:
        selected_options = []

    dic = {}
    treated_blocks = task.treated_blocks.all()
    blocks = task.survey.blocks.all()
    if blocks:
        block = task.survey.blocks.all()[0]
    else:
        return HttpResponseRedirect(reverse('consulting_index'))
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
        form = QuestionsForm(request.POST, dic=dic, selected_options=[])

        if form.is_valid():
            result = Result(patient=task.patient, survey=task.survey, task=task,
                    created_by=request.user, appointment=appointment, block=block)
            result.save()

            if task.task_results.count() == 1:
                task.start_date = result.date
                task.save()

            items = form.cleaned_data.items()
            for name_field, values_list in items:
                if isinstance(values_list, list):
                    for value in values_list:
                        option = get_object_or_404(Option, pk=int(value))
                        result.options.add(option)
                else:
                    option = get_object_or_404(Option, pk=int(values_list))
                    result.options.add(option)

            if block not in treated_blocks:
                task.treated_blocks.add(block)

            if check_task_completion(task.id):
                task.completed = True
                task.end_date = datetime.now()
                task.save()

            return HttpResponseRedirect(reverse('consulting_variables_mark',
                                        args=[id_appointment, result.id]))

    else:
        form = QuestionsForm(dic=dic, selected_options=selected_options)

    return render_to_response(
        'consulting/consultation/monitoring/incomplete_surveys/block.html',
        {'form': form,
        'task': task,
        'appointment': appointment,
        'my_block': block,
        'patient_user': task.patient},
        context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def complete_self_administered_block(request, id_task, id_appointment):
    task = get_object_or_404(Task, pk=int(id_task))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))

    if task.task_results.all():
        last_result = task.task_results.latest('date')

        if last_result:
            selected_options = last_result.options.all()
    else:
        selected_options = []

    dic = {}
    treated_blocks = task.treated_blocks.all()
    blocks = task.survey.blocks.all()
    if blocks:
        block = task.survey.blocks.all()[0]
    else:
        return HttpResponseRedirect(reverse('consulting_index'))
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
        form = QuestionsForm(request.POST, dic=dic, selected_options=[])

        if form.is_valid():
            result = Result(patient=task.patient, survey=task.survey, task=task,
                    created_by=request.user, appointment=appointment)
            result.save()

            if task.task_results.count() == 1:
                task.start_date = result.date
                task.save()

            items = form.cleaned_data.items()
            for name_field, values in items:
                if isinstance(values, list):
                    for value in values:
                        option = Option.objects.get(pk=int(value))
                        result.options.add(option)
                elif values:
                    option = Option.objects.get(pk=int(values))
                    result.options.add(option)

            if block not in treated_blocks:
                task.treated_blocks.add(block)

            if check_task_completion(task.id):
                task.completed = True
                task.end_date = datetime.now()
                task.save()

            return HttpResponseRedirect(
                        reverse('consulting_complete_self_administered_survey',
                                args=[id_appointment]))

    else:
        form = QuestionsForm(dic=dic, selected_options=selected_options)

    return render_to_response(
    'consulting/consultation/monitoring/complete_self_administered/block.html',
    {'form': form,
    'task': task,
    'appointment': appointment,
    'my_block': block,
    'patient_user': task.patient},
    context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def variables_mark(request, id_appointment, id_result):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    variables = get_variables_mark(id_result)
    dimensions = get_dimensions_mark(id_result, variables)
    kind = Result.objects.get(id=id_result).task.treated_blocks.all().aggregate(Max('kind'))['kind__max']

    if kind == settings.GENERAL:
        king =  'General'
    elif kind == settings.EXTENSO:
        kind = 'Extenso'
    else:
        kind = 'Abreviado'



    return render_to_response(
    'consulting/consultation/monitoring/incomplete_surveys/variables_mark.html',
    {'variables': variables,
     'dimensions': dimensions,
     'kind': kind,
    'appointment': appointment,
    'patient_user': appointment.patient},
    context_instance=RequestContext(request))


def get_variables_mark(id_result):
    result = get_object_or_404(Result, pk=int(id_result))
    answers = result.task.get_answers()
    options = result.options.all()
    marks = {}
    variable_tuple = None
    
    kind = result.task.treated_blocks.all().aggregate(Max('kind'))['kind__max']

    #treated_blocks = result.task.treated_blocks.all()
    #ade_block = get_object_or_404(Block,
    #                               code=settings.ANXIETY_DEPRESSION_EXTENSIVE)
    #be_block = get_object_or_404(Block,
    #                               code=settings.BEHAVIOR_EXTENSIVE)
    #ads_block = get_object_or_404(Block,
    #                               code=settings.ANXIETY_DEPRESSION_SHORT)
    #bs_block = get_object_or_404(Block,
    #                                code=settings.BEHAVIOR_SHORT)
    #if ade_block or be_block in treated_blocks:
    #    kind = settings.EXTENSO
    #elif ads_block or bs_block in treated_blocks:
    #    kind = settings.ABREVIADO
    #else:
    #    return HttpResponseRedirect(reverse('consulting_index'))
    if not kind:
         return HttpResponseRedirect(reverse('consulting_index'))
    for f in Formula.objects.filter(kind=kind):
        total = None
        for item in f.polynomial.split('+'):
            for a in answers:
                if a.question.code == item:
                    if not total:
                        total = 0
                    total += a.weight
                    break
            #try:
            #    total += result.options.get(question__code=item).weight
            #except:
            #    pass
        if total != None:
            if f.variable in marks:
                marks[f.variable]+=(float(total) * float(f.factor))
            else:
                marks[f.variable]=(float(total) * float(f.factor))
        else:
            marks[f.variable] = total

    return marks


def get_without_mark_variables(id_result):
    result = get_object_or_404(Result, pk=int(id_result))
    options = result.options.all()
    list_variables = []

    treated_blocks = result.task.treated_blocks.all()
    ade_block = get_object_or_404(Block,
                                    code=settings.ANXIETY_DEPRESSION_EXTENSIVE)
    ads_block = get_object_or_404(Block,
                                    code=settings.ANXIETY_DEPRESSION_SHORT)
    if ade_block in treated_blocks:
        kind = settings.EXTENSO
    elif ads_block in treated_blocks:
        kind = settings.ABREVIADO
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

    variables = Variable.objects.all()
    for variable in variables:
        formulas = variable.variable_formulas.filter(kind=kind)

        mark = 0
        for formula in formulas:
            codes = formula.polynomial.split('+')

            weight = 0
            for code in codes:
                if options.filter(question__code=code):
                    weight = weight + options.get(question__code=code).weight
            mark = mark + (float(weight) * float(formula.factor))

        if mark == 0.0:
            variable = get_object_or_404(Variable, code=variable.code)
            t = variable.id, variable.name
            list_variables.append(t)
    return list_variables

def get_dimensions_mark(id_result, variables_mark=None):
    marks = {}
    if not variables_mark:
        variables_mark = get_variables_mark(id_result)
    for d in Dimension.objects.all():
        total = 0
        for item in d.polynomial.split('+'):
            variable = Variable.objects.get(code=item)
            try:
                total += variables_mark[variable]
            except:
                pass
        if d.name in marks:
            marks[d.name] += (float(total) * float(d.factor))
        else:
            marks[d.name] = (float(total) * float(d.factor))
    return marks



def get_remains_questions(id_result):
    remains_questions = []

    result = get_object_or_404(Result, pk=int(id_result))
    task = result.task
    my_questions = task.questions.all()

    if not my_questions:
        return remains_questions

    blocks = task.survey.blocks.all()
    if blocks:
        block = task.survey.blocks.all()[0]
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

    categories = block.categories.all().order_by('id')
    for category in categories:
        all_questions = category.questions.all().order_by('id')
        for question in all_questions:
            if question not in my_questions:
                remains_questions.append(question)
    return remains_questions


def get_not_assessed_variables(id_result):
    result = get_object_or_404(Result, pk=int(id_result))
    remains_questions = []
    not_assessed_variables = []

    treated_blocks = result.task.treated_blocks.all()
    ade_block = get_object_or_404(Block,
                                    code=settings.ANXIETY_DEPRESSION_EXTENSIVE)
    ads_block = get_object_or_404(Block,
                                    code=settings.ANXIETY_DEPRESSION_SHORT)
    if ade_block in treated_blocks:
        kind = settings.EXTENSO
    elif ads_block in treated_blocks:
        kind = settings.ABREVIADO
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

    remains_questions = get_remains_questions(id_result)

    if remains_questions:
        for question in remains_questions:
            formulas = Formula.objects.filter(kind=kind)
            for formula in formulas:
                codes = formula.polynomial.split('+')
                for code in codes:
                    if question.code == code:
                        t = formula.variable.id, formula.variable.name
                        if t not in not_assessed_variables:
                            not_assessed_variables.append(t)
                        break
    return not_assessed_variables


@login_required()
@only_doctor_consulting
def complete_self_administered_survey(request, id_appointment):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    result = None
    task = None
    warning = None
    variables = None
    symptoms_worsening = []
    more_variables = False
    id_result = None
    try:
        task = Task.objects.get(appointment=appointment,
                                patient=appointment.patient,
                                self_administered=True, completed=True)
        result = task.task_results.latest('date')
        id_result = result.id
        variables = get_variables_mark(result.id)
        not_assessed_variables = get_not_assessed_variables(id_result)

        if not_assessed_variables:
            more_variables = True

        for res in task.task_results.all():
            if res.symptoms_worsening:
                sw = res.symptoms_worsening, res.date
                symptoms_worsening.append(sw)
    except Task.DoesNotExist:
        try:
            task = Task.objects.get(appointment=appointment,
                                patient=appointment.patient,
                                self_administered=True, completed=False)
            task = None
            warning = _(u'Hay encuesta autoadministrada pero no completada')
        except Task.DoesNotExist:
            warning = _(u'No hay encuesta autoadministrada')

    return render_to_response(
    'consulting/consultation/monitoring/complete_self_administered_survey/information.html',
    {'appointment': appointment,
    'id_result': id_result,
    'task': task,
    'variables': variables,
    'more_variables': more_variables,
    'warning': warning,
    'symptoms_worsening': symptoms_worsening,
    'patient_user': appointment.patient},
    context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def select_not_assessed_variables(request, id_appointment, id_result):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    result = get_object_or_404(Result, pk=int(id_result))

    variables = get_not_assessed_variables(result.id)

    if request.method == 'POST':
        form = SelectNotAssessedVariablesForm(request.POST, variables=variables)
        if form.is_valid():
            task = result.task
            if task.survey.code == str(settings.ANXIETY_DEPRESSION_EXTENSIVE):
                kind = settings.EXTENSO
            else:
                kind = settings.ABREVIADO

            id_variables = form.cleaned_data['variables']

            variables = Variable.objects.filter(id__in=id_variables)
            for variable in variables:
                formulas = variable.variable_formulas.filter(kind=kind)
                for formula in formulas:
                    codes = formula.polynomial.split('+')
                    for code in codes:
                        question = get_object_or_404(Question, code=code)
                        if question not in task.questions.all():
                            task.questions.add(question)

            return HttpResponseRedirect(
                        reverse('consulting_complete_self_administered_block',
                                args=[task.id, id_appointment]))
    else:
        form = SelectNotAssessedVariablesForm(variables=variables)

    return render_to_response(
                'consulting/consultation/monitoring/complete_self_administered_survey/select_not_assessed_variables.html',
                {'form': form,
                'appointment': appointment,
                'id_result': result.id,
                'patient_user': appointment.patient},
                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def select_successive_survey(request, id_appointment):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    result = Result.objects.filter(
            Q(patient=appointment.patient,
            task__survey__code=settings.INITIAL_ASSESSMENT) |
            Q(patient=appointment.patient,
            task__survey__code=settings.ANXIETY_DEPRESSION_EXTENSIVE) |
            Q(patient=appointment.patient,
            task__survey__code=settings.ANXIETY_DEPRESSION_SHORT)).latest('date')
    code = result.survey.code

    treated_blocks = result.task.treated_blocks.all()
    ade_block = get_object_or_404(Block,
                        code=settings.ANXIETY_DEPRESSION_EXTENSIVE)
    ads_block = get_object_or_404(Block,
                        code=settings.ANXIETY_DEPRESSION_SHORT)

    if ade_block in treated_blocks:
        kind = settings.EXTENSO
    elif ads_block in treated_blocks:
        kind = settings.ABREVIADO
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

    variables = get_variables(result.id, settings.DEFAULT_NUM_VARIABLES)

    if request.method == 'POST':
        form = SelectOtherTaskForm(request.POST, variables=variables)
        if form.is_valid():
            code_survey = form.cleaned_data['survey']

            if code_survey == str(settings.ANXIETY_DEPRESSION_EXTENSIVE) or\
                code_survey == str(settings.ANXIETY_DEPRESSION_SHORT):
                survey = get_object_or_404(Survey, code=int(code_survey))
            else:
                code_survey = form.cleaned_data['kind']
                if kind == settings.EXTENSO:
                    survey = get_object_or_404(Survey,
                                    code=settings.ANXIETY_DEPRESSION_EXTENSIVE)
                elif kind == settings.ABREVIADO:
                    survey = get_object_or_404(Survey,
                                    code=settings.ANXIETY_DEPRESSION_SHORT)
                else:
                    return HttpResponseRedirect(reverse('consulting_index'))

            task = Task(created_by=request.user, patient=appointment.patient,
            appointment=appointment, self_administered=False, survey=survey)
            task.save()

            id_variables = form.cleaned_data['variables']
            if id_variables:
                variables = Variable.objects.filter(id__in=id_variables)
                for variable in variables:
                    formulas = variable.variable_formulas.filter(kind=kind)
                    for formula in formulas:
                        codes = formula.polynomial.split('+')
                        for code in codes:
                            question = Question.objects.get(code=code)
                            task.questions.add(question)

            return HttpResponseRedirect(reverse('consulting_successive_survey',
                                                args=[task.id, id_appointment]))
    else:
        form = SelectOtherTaskForm(variables=variables)

    return render_to_response(
            'consulting/consultation/monitoring/successive_survey/select.html',
            {'form': form,
            'appointment': appointment,
            'code_variables': settings.VARIABLES,
            'patient_user': appointment.patient},
            context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def successive_block(request, id_task, id_appointment):
    task = get_object_or_404(Task, pk=int(id_task))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))

    if task.task_results.all():
        last_result = task.task_results.latest('date')

        if last_result:
            selected_options = last_result.options.all()
    else:
        selected_options = []

    dic = {}
    treated_blocks = task.treated_blocks.all()
    blocks = task.survey.blocks.all()
    if blocks:
        block = task.survey.blocks.all()[0]
    else:
        return HttpResponseRedirect(reverse('consulting_index'))
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
        form = QuestionsForm(request.POST, dic=dic, selected_options=[])

        if form.is_valid():
            result = Result(patient=task.patient, survey=task.survey, task=task,
                    created_by=request.user, appointment=appointment, block=block)
            result.save()

            if task.task_results.count() == 1:
                task.start_date = result.date
                task.save()

            items = form.cleaned_data.items()
            for name_field, values_list in items:
                if isinstance(values_list, list):
                    for value in values_list:
                        option = Option.objects.get(pk=int(value))
                        result.options.add(option)
                else:
                    option = Option.objects.get(pk=int(values_list))
                    result.options.add(option)

            if block not in treated_blocks:
                task.treated_blocks.add(block)

            if check_task_completion(task.id):
                task.completed = True
                task.end_date = datetime.now()
                task.save()

            return HttpResponseRedirect(reverse('consulting_monitoring',
                                                args=[id_appointment]))

    else:
        form = QuestionsForm(dic=dic, selected_options=selected_options)

    return render_to_response(
    'consulting/consultation/monitoring/successive_survey/block.html',
    {'form': form,
    'task': task,
    'appointment': appointment,
    'my_block': block,
    'patient_user': task.patient},
    context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def prev_treatment_block(request, id_appointment):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))

    at_survey = get_object_or_404(Survey, code=settings.ADHERENCE_TREATMENT)

    task = Task(created_by=request.user, patient=appointment.patient,
                survey=at_survey, appointment=appointment,
                self_administered=False)
    task.save()

    return HttpResponseRedirect(reverse('consulting_treatment_survey',
                                        args=[task.id, id_appointment]))


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
                    for value in values_list:
                        option = get_object_or_404(Option, pk=int(value))
                        result.options.add(option)

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


@login_required()
@only_doctor_consulting
def select_behavior_survey(request, id_appointment):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))

    if request.method == 'POST':
        form = SelectBehaviorSurveyForm(request.POST)
        if form.is_valid():
            code_survey = form.cleaned_data['survey']

            if code_survey == str(settings.BEHAVIOR_EXTENSIVE):
                survey = get_object_or_404(Survey,
                                        code=int(settings.BEHAVIOR_EXTENSIVE))
            elif code_survey == str(settings.BEHAVIOR_SHORT):
                survey = get_object_or_404(Survey,
                                            code=int(settings.BEHAVIOR_SHORT))
            else:
                return HttpResponseRedirect(reverse('consulting_index'))

            task = Task(created_by=request.user, patient=appointment.patient,
            appointment=appointment, self_administered=False, survey=survey)
            task.save()

            return HttpResponseRedirect(reverse('consulting_behavior_survey',
                                    args=[id_appointment, task.id]))
    else:
        form = SelectBehaviorSurveyForm()

    return render_to_response(
            'consulting/consultation/monitoring/behavior_survey/select.html',
            {'form': form,
            'appointment': appointment,
            'patient_user': appointment.patient},
            context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def behavior_block(request, id_appointment, id_task):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    task = get_object_or_404(Task, id=id_task)

    dic = {}
    treated_blocks = task.treated_blocks.all()
    block = task.survey.blocks.all()[0]
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
            result = Result(patient=task.patient, survey=task.survey, task=task,
                    created_by=request.user, appointment=appointment, block=block)
            result.save()

            task.start_date = result.date
            task.save()

            items = form.cleaned_data.items()
            for name_field, values_list in items:
                if isinstance(values_list, list):
                    for value in values_list:
                        option = get_object_or_404(Option, pk=int(value))
                        result.options.add(option)
                else:
                    option = get_object_or_404(Option, pk=int(values_list))
                    result.options.add(option)

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
    'consulting/consultation/monitoring/behavior_survey/block.html',
    {'form': form,
    'id_task': id_task,
    'appointment': appointment,
    'my_block': block,
    'patient_user': task.patient},
    context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def conclusion_monitoring(request, id_appointment):
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

            return HttpResponseRedirect(
                                reverse('consulting_new_medicine_monitoring',
                                        args=[conclusion.id]))
    else:
        form = ConclusionForm()

    return render_to_response(
                'consulting/consultation/monitoring/finish/conclusion.html',
                {'form': form,
                'patient_user': appointment.patient,
                'appointment': appointment},
                context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def new_medicine_monitoring(request, id_conclusion):
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
                                reverse('consulting_new_medicine_monitoring',
                                args=[id_conclusion]))
    else:
        form = MedicineForm()

    return render_to_response(
                'consulting/consultation/monitoring/finish/new_medicine.html',
                {'form': form,
                'id_conclusion': id_conclusion,
                'appointment': conclusion.appointment,
                'patient_user': patient},
                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
@paginate(
    template_name='consulting/consultation/monitoring/finish/list_medicines.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_medicines_before_monitoring(request, id_conclusion):
    conclusion = get_object_or_404(Conclusion, pk=int(id_conclusion))

    medicines = conclusion.conclusion_medicines.filter(
        before_after_first_appointment=settings.BEFORE).order_by('-date')
    template_data = {}
    template_data.update({'patient_user': conclusion.patient,
                        'medicines': medicines,
                        'id_conclusion': id_conclusion,
                        'appointment': conclusion.appointment,
                        'csrf_token': get_token(request)})
    return template_data


@login_required()
@only_doctor_consulting
@paginate(
    template_name='consulting/consultation/monitoring/finish/list_medicines.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_medicines_after_monitoring(request, id_conclusion):
    conclusion = get_object_or_404(Conclusion, pk=int(id_conclusion))

    medicines = conclusion.conclusion_medicines.filter(
        before_after_first_appointment=settings.AFTER).order_by('-date')

    template_data = {}
    template_data.update({'patient_user': conclusion.patient,
                        'medicines': medicines,
                        'id_conclusion': id_conclusion,
                        'appointment': conclusion.appointment,
                        'csrf_token': get_token(request)})
    return template_data


@login_required()
@only_doctor_consulting
def detail_medicine_monitoring(request):
    if request.method == 'POST':
        medicine_id = request.POST.get("medicine_id", "")
        id_conclusion = request.POST.get("id_conclusion", "")
        try:
            medicine = Medicine.objects.get(id=medicine_id)
            conclusion = get_object_or_404(Conclusion, pk=int(id_conclusion))
            return render_to_response(
                        'consulting/consultation/monitoring/finish/detail_medicine.html',
                        {'medicine': medicine,
                        'id_conclusion': conclusion.id,
                        'appointment': conclusion.appointment},
                        context_instance=RequestContext(request))
        except Medicine.DoesNotExist:
                return HttpResponseRedirect(reverse('consulting_index'))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@only_doctor_consulting
@paginate(template_name='consulting/consultation/monitoring/finish/list_medicines_ajax.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def remove_medicine_monitoring(request):
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
                                'id_conclusion': id_conclusion,
                                'appointment': conclusion.appointment})
            return template_data
        except Medicine.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@only_doctor_consulting
def add_illness_monitoring(request, id_conclusion):
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
                                    reverse('consulting_add_illness_monitoring',
                                    args=[id_conclusion]))
    else:
        form = IllnessAddPatientForm(instance=patient.get_profile())

    return render_to_response(
                        'consulting/consultation/monitoring/finish/add_illness.html',
                        {'form': form,
                        'conclusion': conclusion,
                        'appointment': conclusion.appointment,
                        'patient_user': patient,
                        'year': time.localtime()[0]},
                        context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def select_year_month_monitoring(request, year, id_patient, id_appointment):
    patient = get_object_or_404(User, pk=int(id_patient))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    year = int(year)

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
                    patient_user=patient, appointment=appointment)
    return render_to_response(
            "consulting/consultation/monitoring/finish/select_year_month.html",
            data,
            context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
@paginate(template_name='consulting/consultation/monitoring/finish/list_day.html',
    list_name='events', objects_per_page=settings.OBJECTS_PER_PAGE)
def day_monitoring(request, year, month, day, id_patient, id_appointment):
    patient = get_object_or_404(User, pk=int(id_patient))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
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
            events=events, free_intervals=free_intervals, patient_user=patient,
            appointment=appointment, context_instance=RequestContext(request))

    return template_data


@login_required
@only_doctor_consulting
def month_monitoring(request, year, month, change, id_patient, id_appointment):
    patient = get_object_or_404(User, pk=int(id_patient))
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
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
                    month_days=lst, mname=mnames[month - 1], patient_user=patient,
                    appointment=appointment)

    return render_to_response(
            "consulting/consultation/monitoring/finish/month.html",
            template_data, context_instance=RequestContext(request))


@login_required
@only_doctor_consulting
def app_add_monitoring(request, year, month, day, id_patient, id_appointment_monitoring):
    patient = get_object_or_404(User, pk=int(id_patient))
    appointment_monitoring = get_object_or_404(
                                Appointment, pk=int(id_appointment_monitoring))
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
                appointment = form.save()

                return HttpResponseRedirect(
                reverse('consulting_select_self_administered_survey_monitoring',
                        args=[appointment.id]))
            else:
                return render_to_response(
                    "consulting/consultation/monitoring/finish/new_app.html",
                    {'form': form,
                     'year': int(year), 'month': int(month), 'day': int(day),
                     'month_days': lst,
                     'mname': mname,
                     'doctor': doctor,
                     'patient_user': patient,
                     'appointment': appointment_monitoring,
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
    return render_to_response(
                "consulting/consultation/monitoring/finish/new_app.html",
                {'form': form,
                 'year': int(year), 'month': int(month), 'day': int(day),
                 'month_days': lst,
                 'mname': mname,
                 'doctor': doctor,
                 'patient_user': patient,
                 'appointment': appointment_monitoring,
                 'doctor_preferences': doctor_preferences,
                 'free_intervals': free_intervals},
                context_instance=RequestContext(request))


@login_required()
@only_doctor_consulting
def select_self_administered_survey_monitoring(request, id_appointment):
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    result = Result.objects.filter(
            Q(patient=appointment.patient,
            task__survey__code=settings.ANXIETY_DEPRESSION_EXTENSIVE) |
            Q(patient=appointment.patient,
            task__survey__code=settings.ANXIETY_DEPRESSION_SHORT)).latest('date')
    code = result.survey.code
    kind = result.survey.kind

    variables = get_variables(result.id, settings.DEFAULT_NUM_VARIABLES)

    if request.method == 'POST':
        form = SelectTaskForm(request.POST, variables=variables)
        if form.is_valid():
            code_survey = form.cleaned_data['survey']
            from_date = form.cleaned_data['from_date']
            to_date = form.cleaned_data['to_date']

            if code_survey == str(settings.ANXIETY_DEPRESSION_EXTENSIVE) or\
                code_survey == str(settings.ANXIETY_DEPRESSION_SHORT):
                survey = get_object_or_404(Survey, code=int(code_survey))
            else:
                treated_blocks = result.task.treated_blocks.all()
                ade_block = get_object_or_404(Block,
                                    code=settings.ANXIETY_DEPRESSION_EXTENSIVE)
                ads_block = get_object_or_404(Block,
                                    code=settings.ANXIETY_DEPRESSION_SHORT)
                if ade_block in treated_blocks:
                    kind = settings.EXTENSO
                    survey = get_object_or_404(Survey,
                                    code=settings.ANXIETY_DEPRESSION_EXTENSIVE)
                elif ads_block in treated_blocks:
                    kind = settings.ABREVIADO
                    survey = get_object_or_404(Survey,
                                    code=settings.ANXIETY_DEPRESSION_SHORT)
                else:
                    return HttpResponseRedirect(reverse('consulting_index'))

            task = Task(created_by=request.user, patient=appointment.patient,
            appointment=appointment, self_administered=True, survey=survey,
            from_date=from_date, to_date=to_date)
            task.save()

            id_variables = form.cleaned_data['variables']
            if id_variables:
                variables = Variable.objects.filter(id__in=id_variables)
                for variable in variables:
                    formulas = variable.variable_formulas.filter(kind=kind)
                    for formula in formulas:
                        codes = formula.polynomial.split('+')
                        for code in codes:
                            question = get_object_or_404(Question, code=code)
                            task.questions.add(question)

            return HttpResponseRedirect(reverse('consulting_today'))
    else:
        form = SelectTaskForm(variables=variables)

    return render_to_response(
            'consulting/consultation/monitoring/finish/select_self_administered_survey.html',
            {'form': form,
            'appointment': appointment,
            'code_variables': settings.VARIABLES,
            'patient_user': appointment.patient,
            'appointment': appointment},
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
    tasks = Task.objects.filter(patient=request.user,
                                    self_administered=True, completed=False,
                                    to_date__gte=datetime.now(),
                                    from_date__lte=datetime.now())\
                                    .order_by('-creation_date')
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
@only_doctor_consulting

@paginate(template_name='consulting/patient/list_medicines.html',
    list_name='medicines', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_medicines(request):
    logged_user_profile = request.user.get_profile()

    patient_user_id = request.session['patient_user_id']

    patient_user = User.objects.get(id=patient_user_id)

    if request.GET and request.GET.get('when', '') == 'before':
        when = settings.BEFORE
    else:
        when = settings.AFTER
    medicines = Medicine.objects.filter(patient=patient_user,
    before_after_first_appointment=when).order_by('-date')

    template_data = {}
    template_data.update({'patient_user': patient_user,
                            'medicines': medicines,
                            'when': when,
                            'patient_user_id': patient_user_id,
                            'csrf_token': get_token(request)})
    return template_data

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
        return render_to_response('consulting/stadistic/stratification.html', {},
                            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

############################## REPORTS ########################################
@login_required
@only_doctor_consulting
def view_report(request, id_task):
    task = get_object_or_404(Task, pk=int(id_task))
    if task.survey.id > settings.INITIAL_ASSESSMENT:
        return HttpResponseRedirect(reverse('consulting_index'))
    else:
        patient = task.patient.get_profile()
        marks = get_variables_mark(task.task_results.all()[0].id) # FIX IT!!!!
        dimensions = get_dimensions_mark(None, marks)
        beck_mark = task.calculate_beck_mark()
        hamilton_mark, hamilton_submarks = task.calculate_hamilton_mark()
        ave_mark = task.calculate_mark_by_code('AVE')
        light_mark = task.calculate_mark_by_code('L')
        blaxter_mark = task.calculate_mark_by_code('AS')
        medicines = Medicine.objects.filter(patient=task.patient,
        before_after_first_appointment=settings.BEFORE).order_by('-date')

        recurrent = beck_mark > 13 and task.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(code__in=['AP4','AP5','AP6'])
        recurrent = recurrent or (hamilton_mark > 18 and task.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(code__in=['AP1','AP3']))
        try:
            h6 = hamilton_submarks['H6']
        except:
            h6 = None

        if request.GET and request.GET.get('as', '') == 'pdf':
            mypdf = PDFTemplateView()
            mypdf.request=request
            mypdf.filename ='Consulting30_report.pdf'
            mypdf.header_template = 'ui/includes/pdf_header.html'
            mypdf.template_name='consulting/consultation/report/base.html'
            return mypdf.render_to_response(context={'as_pdf':True,
                                    'task': task,
                                    'marks': marks,
                                    'conclusion':Conclusion.objects.filter(task=task).latest('date'),
                                    'patient': patient,
                                    'beck_mark':beck_mark,
                                    'beck_scale':task.get_depression_status(),
                                    'time_interval': task.get_time_interval(),
                                    'hamilton_mark':hamilton_mark,
                                    'hamilton_scale': task.get_anxiety_status(),
                                    'h6_mark': h6,
                                    'ave_mark':ave_mark,
                                    'ave_status':task.get_ave_status(),
                                    'recurrent':recurrent,
                                    'somatic_mark':dimensions[u'Somática'],
                                    'cognitive_mark':dimensions[u'Cognitiva'],
                                    'light_mark':light_mark,
                                    'blaxter_mark':blaxter_mark,
                                    'af_dict':task.get_af_dict(),
                                    'ap_list':task.get_ap_list(),
                                    'rp_list':task.get_rp_list(),
                                    'as_mark':task.calculate_mark_by_code('AS'),
                                    'organicity_list':task.get_organicity_list(),
                                    'medicaments_list':medicines,})
        else:
            return render_to_response('consulting/consultation/report/base.html',
                                    {'task': task,
                                    'marks': marks,
                                    'patient': patient,
                                    'conclusion':Conclusion.objects.filter(task=task).latest('date'),
                                    'beck_mark':beck_mark,
                                    'beck_scale':task.get_depression_status(),
                                    'time_interval': task.get_time_interval(),
                                    'hamilton_mark':hamilton_mark,
                                    'hamilton_scale': task.get_anxiety_status(),
                                    'h6_mark': h6,
                                    'ave_mark':ave_mark,
                                    'ave_status':task.get_ave_status(),
                                    'recurrent':recurrent,
                                    'somatic_mark':dimensions[u'Somática'],
                                    'cognitive_mark':dimensions[u'Cognitiva'],
                                    'light_mark':light_mark,
                                    'blaxter_mark':blaxter_mark,
                                    'af_dict':task.get_af_dict(),
                                    'ap_list':task.get_ap_list(),
                                    'rp_list':task.get_rp_list(),
                                    'as_mark':task.calculate_mark_by_code('AS'),
                                    'organicity_list':task.get_organicity_list(),
                                    'medicaments_list':medicines,},
                                    context_instance=RequestContext(request))


@login_required()
@paginate(template_name='consulting/patient/list_reports.html',
    list_name='reports', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_reports(request):
    logged_user_profile = request.user.get_profile()

    patient_user_id = request.session['patient_user_id']

    if logged_user_profile.is_doctor():
        patient_user = User.objects.get(id=patient_user_id)

        reports = Task.objects.filter(patient=patient_user,survey__id__in=[settings.PREVIOUS_STUDY, settings.INITIAL_ASSESSMENT], completed=True).order_by('-end_date')

        template_data = {}
        template_data.update({'patient_user': patient_user,
                                'reports': reports,
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

    patient_user = User.objects.get(id=patient_user_id)

    tasks = Task.objects.filter(patient=patient_user,survey__id__in=[settings.ANXIETY_DEPRESSION_EXTENSIVE, settings.ANXIETY_DEPRESSION_SHORT, settings.BEHAVIOR_SHORT, settings.BEHAVIOR_EXTENSIVE
    , settings.INITIAL_ASSESSMENT], completed=True).order_by('-end_date')[:5]
    latest_marks = {}
    ticks = []
    for t in tasks:
        for var, mark in get_variables_mark(t.task_results.all()[0].id).items():
            if mark != None:
                if var.name in latest_marks.keys():
                    latest_marks[var.name].append([t.end_date, mark])
                else:
                    latest_marks[var.name] = [[t.end_date, mark]]
            if not t.end_date in ticks:
                ticks.append(t.end_date)
    ticks.sort()

    return render_to_response('consulting/patient/user_evolution.html', 
                                {'patient_user':patient_user,
                                 'latest_marks': latest_marks,
                                 'ticks':ticks},
                            context_instance=RequestContext(request))