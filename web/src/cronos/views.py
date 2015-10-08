# -*- encoding: utf-8 -*-
from datetime import date, datetime, timedelta

from decorators import *
import json
import hashlib
import requests

from django.conf import settings
from django.db.models import Q
from django.middleware.csrf import get_token
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseForbidden
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.contrib.auth.forms import AuthenticationForm
from django.views.decorators.csrf import csrf_exempt

from userprofile.models import get_or_create_CRONOS_user, Profile
from consulting.models import Task, Conclusion
from cal.models import Appointment

from illness.forms import IllnessSelectionForm
from consulting.forms import ConclusionForm
from consulting.views import report as consulting_view_report


def cronos_login(request):
    return render_to_response('400.html', {'error':u"El acceso directo a la aplicación no está habilitado. Por favor, acceda desde la plataforma adecuada"},
                context_instance=RequestContext(request))

def cronos_logout(request):
    logout(request)
    return render_to_response('logout.html', {'error':u"Sesión cerrada con éxito. Para acceder de nuevo, cierre esta ventana y acceda desde la plataforma adecuada"},
                context_instance=RequestContext(request))

def start_point(request, portal=None):
    form = AuthenticationForm()
    if request.method == 'GET':
        id_doctor=request.GET.get('username')
        id_patient=request.GET.get('nuhsa')
        token=request.GET.get('token')
        password=request.GET.get('password')
    elif request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        id_patient=request.POST.get('nuhsa')
        form.is_valid()
        try:
            id_doctor=form.cleaned_data['username']
            password=form.cleaned_data['password']
        except:
            id_doctor = None

    if id_doctor and request.user.username != id_doctor:
        logout(request)
    if id_patient and request.user.username != id_patient:
        logout(request)

    if request.user.is_authenticated():
        if (request.user.get_profile().is_doctor() or request.user.get_profile().is_nurse()) and 'appid' in request.session:
            appointment = Appointment.objects.get(id=request.session['appid'])
            if id_patient is None or appointment.patient.get_profile().medical_number == id_patient:
                return HttpResponseRedirect(reverse('cronos_tasks'))
        elif request.user.get_profile().is_patient():
            return HttpResponseRedirect(reverse('consulting_index'))

    if not id_patient:
        return render_to_response('400.html', {'error':u"ID paciente no especificado"},
                context_instance=RequestContext(request))
    elif portal == 'medico' and not id_doctor:
        return render_to_response('400.html', {'error':u"Usuario no especificado"},
                context_instance=RequestContext(request))
    elif (portal == 'enfermero' and not id_doctor):
        return render_to_response('registration/login.html', {'nuhsa':id_patient, 'form':form},
                context_instance=RequestContext(request))

    authenticated = False
    if portal == 'medico':
        ### Validate against CRONOS API
        authentication = __oAuth(id_doctor, token, portal)
        if authentication == 'true':
            birthdate=request.GET.get('fecha')
            gender=request.GET.get('sexo')
            doctor = get_or_create_CRONOS_user(id_doctor, settings.DOCTOR)
            patient = get_or_create_CRONOS_user(id_patient, settings.PATIENT, doctor.user)
            if birthdate:
                try:
                    patient.dob = datetime.strptime(birthdate, '%Y-%m-%d').date()
                except: 
                    pass
            if gender == 'M':
                patient.sex = settings.MAN
            elif gender == 'F':
                patient.sex = settings.WOMAN
            patient.save()
            authenticated = True
    elif portal == 'paciente':
        ### Validate against CRONOS API
        authentication = __oAuth(id_patient, password, portal)
        if authentication == 'true':
            patient = get_or_create_CRONOS_user(id_patient, settings.PATIENT)
            authenticated = True
    elif portal == 'enfermero':
        ### Validate against CRONOS API
        authentication =  __oAuth(id_doctor, password, portal)
        if authentication == 'true':
            doctor = get_or_create_CRONOS_user(id_doctor, settings.NURSE)
            patient = get_or_create_CRONOS_user(id_patient, settings.PATIENT)
            authenticated = True
        else:
            return render_to_response('registration/login.html', {'nuhsa':id_patient, 'form':form},
                context_instance=RequestContext(request))
    else:
        return render_to_response('400.html', {'error':u"Portal no especificado"},
                context_instance=RequestContext(request))

    if not authenticated:
        print authentication
        return render_to_response('400.html', {'error':u"Autenticación fallida: %s. Revise las credenciales introducidas o contacte con el administrador de la aplicación" % authentication},
                context_instance=RequestContext(request))
    if id_doctor:
        user = authenticate(username=id_doctor, password=settings.SECRET_KEY)
        if user is not None:
            if user.is_active:
                login(request, user)
                request.session['cronos'] = True
                apppointment = Appointment.objects.create(
                    doctor=doctor.user,
                    patient=patient.user,
                    date=date.today(),
                    start_time=datetime.now().time(),
                    end_time=(datetime.now()+timedelta(seconds=5*60)).time(),
                    duration=5,
                    notify=False,
                    description="CRONOS")
                request.session['appid'] = apppointment.id
                return HttpResponseRedirect(reverse('cronos_tasks'))
            else:
                return render_to_response('400.html', {'error':u"Cuenta desactivada. Contacte con el administrador de la aplicación"},
                context_instance=RequestContext(request))
        else:
            raise Http404
    elif id_patient:
        user = authenticate(username=id_patient, password=settings.SECRET_KEY)
        if user is not None:
            if user.is_active:
                login(request, user)
                request.session['cronos'] = True
                return HttpResponseRedirect(reverse('consulting_index'))
            else:
                return render_to_response('400.html', {'error':u"Cuenta desactivada. Contacte con el administrador de la aplicación"},
                context_instance=RequestContext(request))
        else:
            raise Http404
    



def __oAuth(username, password, portal):
    if portal == 'paciente':
         payload = {'nuhsa': username, 'password': password, 'method': 'comprobarPaciente'}
    else:
        if portal == 'enfermero':
            password = hashlib.md5(password).hexdigest()
        payload = {'user': username, 'password': password, 'method': 'checkUser'}
    r = requests.get(settings.AT4_SERVER+settings.AUTH_RESOURCE, params=payload, verify=False)
    return r.text

@csrf_exempt
def fake_auth(request):
    if request.method == "GET":
        print request.GET
        if request.GET.get('password',False):
            return HttpResponse('true')
        else:
            return HttpResponse('Paciente o password incorrectos')
    else:
        raise Http404


@login_required()
@paginate(template_name='cronos/list.html',
    list_name='reports', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_tasks(request):
    if 'appid' in request.session:
        id_appointment = request.session['appid']
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    logged_user_profile = request.user.get_profile()
    #patient_user_id = request.session['patient_user_id']
    code_illness = ''
    if logged_user_profile.is_doctor() or logged_user_profile.is_nurse():
        patient_user = appointment.patient
        link = None
        filters = Q(patient=patient_user) & Q(start_date__isnull=False)
        if logged_user_profile.is_nurse():
            filters &= Q(created_by=request.user)
        if request.method == 'POST':
            form = IllnessSelectionForm(request.POST,
                                       id_appointment=appointment.id)
            if form.is_valid():
                code_illness = form.cleaned_data['illness']
                if code_illness:
                    request.session["notes"] = ''
                    filters = filters & Q(survey__surveys_illnesses__code=code_illness)
                    link = reverse('consulting_select_successive_survey',
                            kwargs={'id_appointment':id_appointment, 
                                    'code_illness': code_illness})
        else:
            form = IllnessSelectionForm(id_appointment=id_appointment)

        reports = Task.objects.filter(filters).order_by('-updated_at')

        template_data = {}
        template_data.update({'form': form,
                                'link': link,
                                'appointment': appointment,
                                'reports': reports,
                                'patient_user': patient_user,
                                'code_illness': code_illness,
                                'csrf_token': get_token(request)})
        return template_data
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

@login_required()
@only_doctor_consulting
@paginate(template_name='cronos/list_recommendations.html',
    list_name='conclusions', objects_per_page=settings.OBJECTS_PER_PAGE)
def recommendations(request):
    if 'appid' in request.session:
        id_appointment = request.session['appid']
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    logged_user_profile = request.user.get_profile()
    #patient_user_id = request.session['patient_user_id']
    if logged_user_profile.is_doctor():
        patient_user = appointment.patient
        filters = Q(patient=patient_user)
        

        conclusions = Conclusion.objects.filter(appointment__patient=appointment.patient).order_by('-updated_at')

        template_data = {}
        template_data.update({  'appointment': appointment,
                                'conclusions': conclusions,
                                'patient_user': patient_user,
                                'csrf_token': get_token(request)})
        return template_data
    else:
        return HttpResponseRedirect(reverse('consulting_index'))

@login_required
@only_doctor_consulting
def edit_recommendation(request, id_conclusion=None):
    if 'appid' in request.session:
        id_appointment = request.session['appid']
        appointment = get_object_or_404(Appointment, pk=int(id_appointment))

    if id_conclusion:
        conclusion = get_object_or_404(Conclusion, pk=int(id_conclusion))
    elif not id_conclusion:
        try:
            conclusion = Conclusion.objects.get(appointment=appointment)
            conclusion.pk = None
        except:
            conclusion = Conclusion()

    if request.method == 'POST':
        form = ConclusionForm(request.POST, instance=conclusion)
        if form.is_valid():
            action = request.POST.get('action', 'save')
            if action == 'save':
                conclusion = form.save(commit=False)
                conclusion.created_by = request.user
                conclusion.patient = appointment.patient
                conclusion.appointment = appointment
                if 'extra' in request.FILES:
                    conclusion.extra = request.FILES['extra']
                conclusion.save()
            elif action == 'delete':
                conclusion.delete()

            return HttpResponseRedirect(
                                reverse('cronos_recommendations',
                                        kwargs={}))
    else:
        if not conclusion.observation and 'notes' in request.session:
            conclusion.observation=request.session["notes"]
        form = ConclusionForm(instance=conclusion)

    return render_to_response(
                'consulting/consultation/monitoring/finish/conclusion.html',
                {'form': form,
                'conclusion': conclusion,
                'patient_user': appointment.patient,
                'appointment': appointment,
                },
                context_instance=RequestContext(request))

def pending_survey(request):
    if request.method == 'GET':
        paciente = get_object_or_404(Profile, medical_number=request.GET.get('nuhsa'))
        n = len(paciente.get_pending_tasks())
        return HttpResponse(n)
    else:
        return render_to_response('400.html', {'error':u"Método no soportado"},
                context_instance=RequestContext(request))

def view_report(request, id_task):
    if request.GET.get('as') == 'pdf':
        token = request.GET.get('token')
        task = get_object_or_404(Task, id=int(id_task))
        if token == hashlib.md5(task.patient.get_profile().medical_number).hexdigest():
            return consulting_view_report(request, id_task)
        else:
            return HttpResponseForbidden('Invalid token')


@login_required()
@only_doctor_consulting
@paginate(template_name='cronos/list_video.html',
    list_name='videos', objects_per_page=settings.OBJECTS_PER_PAGE)
def videoconferences(request):
    if 'appid' in request.session:
        id_appointment = request.session['appid']
    appointment = get_object_or_404(Appointment, pk=int(id_appointment))
    
    url = settings.VIDEOCONFERENCE_SERVER + '/apiCronos/v1/videoConferences/stats/' + appointment.patient.username
    try:
        r = requests.get(url, timeout=15, verify=False)
        data = r.json()['data']['sessions']
        data.reverse()
    except:
        data = []
    
    template_data = {'videos': data, 'patient_user': appointment.patient,
                'appointment': appointment}
    return template_data