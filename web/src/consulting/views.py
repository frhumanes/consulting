# -*- encoding: utf-8 -*-
from datetime import datetime
from random import randint
from django.middleware.csrf import get_token
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.core.mail import send_mail
from decorators import paginate
from userprofile.models import Profile
from userprofile.forms import ProfileForm
from consulting.forms import MedicineForm
from cal.forms import AppointmentForm
from consulting.models import Medicine
from cal.models import Appointment
from consulting.helper import strip_accents
from medicament.models import Component, Group


#################################### INDEX ####################################
@login_required()
def index(request):

    logged_user_profile = request.user.get_profile()

    if logged_user_profile.role == settings.DOCTOR:
        return render_to_response('consulting/index_doctor.html', {},
                                context_instance=RequestContext(request))
    elif logged_user_profile.role == settings.ADMINISTRATIVE:
        return render_to_response('consulting/index_administrative.html', {},
                                context_instance=RequestContext(request))
    else:
        #profile.role == settings.PATIENT
        return render_to_response('consulting/index_patient.html', {},
                                context_instance=RequestContext(request))


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
            form = ProfileForm(request.POST, exclude_list=exclude_list)
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
                            profile.doctor = User.objects.get(
                                            profile=logged_user_profile)
                        profile.user = user
                        profile.save()
                    except Exception:
                        user.delete()
                        return HttpResponseRedirect(
                                                reverse('consulting_index'))
                    ###########################################################

                    #Relationships between doctor and her/his patients
                    if logged_user_profile.is_doctor():
                        logged_user_profile.patients.add(user)
                        logged_user_profile.save()

                    #SEND EMAIL
                    sendemail(user)

                    return render_to_response(
                                'consulting/patient_identification.html',
                                {'patient_user': user,
                                'patient_user_id': user.id,
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

        return render_to_response('consulting/patient.html',
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
                                    'consulting/patient_identification.html',
                                    {'patient_user': user,
                                    'patient_user_id': patient_user_id,
                                    'next': next},
                                    context_instance=RequestContext(request))
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))
    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def searcher(request):
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
            users = User.objects.filter(profile__id__in=profiles)

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
                form = ProfileForm(request.POST, instance=profile,
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
                    return render_to_response('consulting/patient.html',
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

            return render_to_response('consulting/patient.html',
                                    {'form': form,
                                    'edit': True,
                                    'patient_user_id': patient_user_id,
                                    'next': next},
                                    context_instance=RequestContext(request))
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def set_patient_pm(request, patient_user_id):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        request.session['patient_user_id'] = patient_user_id
        try:
            patient_user = User.objects.get(id=patient_user_id)
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

            return render_to_response('consulting/personal_data_pm.html',
                        {'patient_user_id': patient_user.id,
                        'patient_user': patient_user},
                        context_instance=RequestContext(request))
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


################################# APPOINTMENT #################################
@login_required()
def newappointment(request, newpatient_id):
    logged_user_profile = request.user.get_profile()
    doctor = None

    if logged_user_profile.is_doctor() or\
     logged_user_profile.is_administrative():
        try:
            patient_user = User.objects.get(id=newpatient_id)
            patient_profile = patient_user.get_profile()
            # CHECK IF DOCTOR CONTAINS THIS PATIENT
            if logged_user_profile.is_doctor():
                if not patient_user in logged_user_profile.patients.all():
                    return HttpResponseRedirect(reverse('consulting_index'))
        except User.DoesNotExist:
            return HttpResponseRedirect(reverse('consulting_index'))

        if request.method == "POST":
            # EXCLUDE DOCTOR OR NOT
            if (patient_user.patientappointments.count() == 0 and\
                logged_user_profile.is_doctor()):
                    form = AppointmentForm(request.POST, readonly_doctor=True,
                                        doctor_user=logged_user_profile.user)
            elif patient_user.patientappointments.count() > 0:
                form = AppointmentForm(request.POST, readonly_doctor=True,
                                        doctor_user=patient_profile.doctor)
            else:
                form = AppointmentForm(request.POST, readonly_doctor=False,
                                        doctor_user=None)

            if form.is_valid():
                # RELATIONSHIP BETWEEN PATIENT AND DOCTOR IF PATIENT HASN'T GOT
                # APPOINTMENTS
                if patient_user.patientappointments.count() == 0:
                    if logged_user_profile.is_doctor():
                        # UPDATE PATIENT
                        patient_profile.doctor = logged_user_profile.user
                        patient_profile.save()
                        # UPDATE DOCTOR
                        logged_user_profile.patients.add(patient_user)
                        logged_user_profile.save()
                    if logged_user_profile.is_administrative():
                        # UPDATE PATIENT
                        doctor_user = form.cleaned_data['doctor']
                        patient_profile.doctor = doctor_user
                        patient_profile.save()
                        # UPDATE DOCTOR
                        doctor_user.get_profile().patients.add(patient_user)
                        doctor_user.save()

                # CREATE APPOINTMENT
                appointment = form.save(commit=False)
                # SAVE DOCTOR IN NEW APPOINTMENT
                if (patient_user.patientappointments.count() == 0 and\
                    logged_user_profile.is_doctor()):
                    appointment.doctor = logged_user_profile.user
                elif patient_user.patientappointments.count() > 0:
                    appointment.doctor = patient_profile.doctor
                else:
                    appointment.doctor = form.cleaned_data['doctor']
                # SAVE PATIENT IN NEW APPOINTMENT
                appointment.patient = patient_user
                # SAVE STATUS IN NEW APPOINTMENT
                appointment.status = settings.UNRESOLVED
                appointment.save()

                return render_to_response(
                    'consulting/newappointment_datas.html',
                    {'appointment': appointment},
                    context_instance=RequestContext(request))
        else:
            # EXCLUDE DOCTOR OR NOT
            if (patient_user.patientappointments.count() == 0 and\
                logged_user_profile.is_doctor()):
                    doctor = logged_user_profile.user
                    form = AppointmentForm(readonly_doctor=True,
                                        doctor_user=doctor)
            elif patient_user.patientappointments.count() > 0:
                doctor = patient_profile.doctor
                form = AppointmentForm(readonly_doctor=True,
                                        doctor_user=doctor)
            else:
                form = AppointmentForm(readonly_doctor=False,
                                        doctor_user=None)
        return render_to_response(
                    'consulting/newappointment.html',
                    {'form': form,
                    'patient_user': patient_user,
                    'newpatient_id': newpatient_id,
                    'doctor': doctor},
                    context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def appointments_doctor(request):
    if request.method == 'POST':
        doctor_id = request.POST.get("doctor_id", "")
        try:
            # We check doctor user exit
            doctor_user = User.objects.get(id=doctor_id)
            appointments_doctor = Appointment.objects.filter(
                                    doctor=doctor_user)
        except User.DoesNotExit:
            return HttpResponseRedirect(reverse('consulting_index'))

    return render_to_response('consulting/list_appointments_doctor_ajax.html',
                            {'appointments': appointments_doctor},
                            context_instance=RequestContext(request))


@paginate(template_name='consulting/list_patient_appointments.html',
        list_name='patient_appointments',
        objects_per_page=settings.OBJECTS_PER_PAGE)
def patient_appointments(request, patient_user_id):
    try:
        patient_user = User.objects.get(id=patient_user_id)
    except User.DoesNotExist:
        return HttpResponseRedirect(reverse('consulting_index'))

    patient_appointments = Appointment.objects.filter(
                                                patient=patient_user)
    template_data = {}
    template_data.update({'patient_appointments': patient_appointments,
                            'patient_user': patient_user})
    return template_data


@login_required()
def patient_management(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        return render_to_response('consulting/index_pm.html', {},
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
            form = MedicineForm(request.POST)
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
                    'consulting/new_medicine_pm.html',
                    {'form': form,
                    'patient_user_id': patient_user_id,
                    'patient_user': patient_user},
                    context_instance=RequestContext(request))
    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@paginate(template_name='consulting/list_medicines_pm.html',
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
@paginate(template_name='consulting/list_medicines_pm.html',
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

                return render_to_response('consulting/detail_medicine.html',
                    {'medicine': medicine},
                        context_instance=RequestContext(request))
            except Medicine.DoesNotExist:
                    return HttpResponseRedirect(reverse('consulting_index'))

    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@paginate(template_name='consulting/list_medicines_ajax_pm.html',
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
        return render_to_response('consulting/index_administration.html', {},
                            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


################################## STADISTICS #################################
@login_required()
def stratification(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        return render_to_response('consulting/stratification.html', {},
                            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))
