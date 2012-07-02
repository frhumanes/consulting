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
from consulting.forms import AppointmentForm, PrescriptionForm
from consulting.models import Appointment, Treatment, Prescription
from consulting.helper import strip_accents
from medicament.models import Component, Group


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


def create_or_update_profile(user, form, username, role):
    name = format_string(form.cleaned_data['name'])
    first_surname = format_string(form.cleaned_data['first_surname'])
    second_surname = format_string(form.cleaned_data['second_surname'])
    nif = form.cleaned_data['nif']

    try:
        profile = user.get_profile()
    except Profile.DoesNotExist:
        profile = Profile()
        profile.user = user

    profile.username = username
    profile.name = name
    profile.first_surname = first_surname
    profile.second_surname = second_surname
    profile.nif = nif
    profile.email = form.cleaned_data['email']
    profile.sex = form.cleaned_data['sex']
    profile.address = form.cleaned_data['address']
    profile.town = form.cleaned_data['town']

    if form.cleaned_data['postcode']:
        profile.postcode = form.cleaned_data['postcode']
    else:
        profile.postcode = None

    profile.dob = form.cleaned_data['dob']
    profile.status = form.cleaned_data['status']

    if not form.cleaned_data['status']:
        profile.status = -1
    else:
        profile.status = form.cleaned_data['status']

    profile.phone1 = form.cleaned_data['phone1']
    profile.phone2 = form.cleaned_data['phone2']
    profile.profession = form.cleaned_data['profession']
    profile.role = role

    profile.save()


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
            form = ProfileForm(request.POST)
            if form.is_valid():
                username = generate_username(form)
                try:
                    Profile.objects.get(username=username)
                    same_username = True
                except Profile.DoesNotExist:
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
                    user.profile = create_or_update_profile(user,
                                    form, username, settings.PATIENT)
                    user.save()

                    if logged_user_profile.is_doctor():
                        # Update doctor
                        logged_user_profile.patients.add(user)
                        logged_user_profile.save()
                        # Update patient
                        doctor_user = User.objects.get(
                                        profile=logged_user_profile)
                        patient_profile = user.get_profile()
                        patient_profile.doctor = doctor_user
                        patient_profile.save()

                    # SEND EMAIL
                    sendemail(user)

                    return render_to_response(
                                'consulting/patient_identification.html',
                                {'patient_user': user,
                                'patient_user_id': user.id,
                                'newpatient': True},
                                context_instance=RequestContext(request))
        else:
            form = ProfileForm()

        return render_to_response('consulting/patient.html',
                                    {'form': form,
                                    'same_username': same_username},
                                    context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


def update_user(user, form, new_username):
    user.username = new_username
    user.set_password(settings.DEFAULT_PASSWORD)
    user.first_name = format_string(form.cleaned_data['name'])
    user.last_name = format_string(
                        form.cleaned_data['first_surname'])\
                        + ' ' +\
                format_string(
                        form.cleaned_data['second_surname'])
    user.email = form.cleaned_data['email']
    user.profile = create_or_update_profile(
                                    user, form, new_username, settings.PATIENT)
    user.save()


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
                form = ProfileForm(request.POST, instance=profile)
                if form.is_valid():
                    old_username = user.username
                    new_username = generate_username(form)
                    update_user(user, form, new_username)
                    if not new_username == old_username:
                        sendemail(user)
                        patient_user_id = user.id
                        return HttpResponseRedirect(
                            '%s?next=%s' % (
                            reverse('consulting_patient_identification_pm',
                                    args=[patient_user_id]),
                            redirect_to))
                    else:
                        return HttpResponseRedirect(redirect_to)
            else:
                next = request.GET.get('next', '')
                data = get_profile_data(profile)
                form = ProfileForm(initial=data)

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


def get_profile_data(profile):
    data = {'name': profile.name,
            'first_surname': profile.first_surname,
            'second_surname': profile.second_surname,
            'nif': profile.nif,
            'sex': profile.sex,
            'address': profile.address,
            'town': profile.town,
            'postcode': profile.postcode,
            'status': profile.status,
            'dob': profile.dob,
            'phone1': profile.phone1,
            'phone2': profile.phone2,
            'email': profile.email,
            'profession': profile.profession
            }

    return data


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


@login_required()
def personal_data_pm(request, patient_user_id):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        request.session['patient_user_id'] = patient_user_id
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


@login_required()
@paginate(template_name='consulting/list_treatments_pm.html',
    list_name='treatments', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_treatments_pm(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        patient_user_id = request.session['patient_user_id']
        patient_user = User.objects.get(id=patient_user_id)

        treatments = Treatment.objects.filter(patient=patient_user).\
                                                order_by('-date')

        template_data = {}
        template_data.update({'patient_user': patient_user,
                                'treatments': treatments,
                                'patient_user_id': patient_user_id,
                                'csrf_token': get_token(request)})
        return template_data
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def detail_treatment_pm(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        if request.method == 'POST':
            treatment_id = request.POST.get("treatment_id", "")
            try:
                treatment = Treatment.objects.get(id=treatment_id)

                return render_to_response('consulting/detail_treatment.html',
                    {'prescriptions': treatment.treatmentprescriptions.all()},
                        context_instance=RequestContext(request))
            except Treatment.DoesNotExist:
                    return HttpResponseRedirect(reverse('consulting_index'))

    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def newtreatment_pm(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        patient_user_id = request.session['patient_user_id']
        patient_user = User.objects.get(id=patient_user_id)

        treatment = Treatment(patient=patient_user,
                                from_appointment=False,
                                date=datetime.now())
        treatment.save()

        return HttpResponseRedirect(
            reverse('consulting_add_prescriptions_treatment_pm',
            args=[treatment.id]))

    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def add_prescriptions_treatment_pm(request, treatment_id):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        patient_user_id = request.session['patient_user_id']
        patient_user = User.objects.get(id=patient_user_id)

        if request.method == "POST":
            try:
                treatment = Treatment.objects.get(id=treatment_id)
                form = PrescriptionForm(request.POST)
                if form.is_valid():
                    # MEDICINE CAN BE NEW OR ALREADY EXISTED
                    component_name = form.cleaned_data['searcher_component']
                    kind_component = form.cleaned_data['kind_component']
                    try:
                        component = Component.objects.get(name=component_name,
                                    kind_component=kind_component)
                        prescription = form.save(commit=False)
                        prescription.treatment = treatment
                        prescription.component = component
                        prescription.save()
                    except Component.DoesNotExist:
                        component_group = Group.objects.get(id=-1)
                        component = Component(name=component_name,
                                            kind_component=kind_component)
                        component.save()
                        component.groups.add(component_group)
                        component.save()

                        prescription = Prescription(treatment=treatment,
                                component=component,
                                before_after=form.cleaned_data['before_after'],
                                months=form.cleaned_data['months'],
                                posology=form.cleaned_data['posology'])
                        prescription.save()
                    #INICIALIZE FORM
                    form = PrescriptionForm()
                else:
                    # ONLY GET TREATMENT OBJECT TO CAN GET ITS PRESCRIPTIONS
                    try:
                        treatment = Treatment.objects.get(id=treatment_id)
                    except Treatment.DoesNotExist:
                        return HttpResponseRedirect(
                                                reverse('consulting_index'))
            except Treatment.DoesNotExist:
                return HttpResponseRedirect(reverse('consulting_index'))
        else:
            form = PrescriptionForm()

            try:
                treatment = Treatment.objects.get(id=treatment_id)
            except Treatment.DoesNotExist:
                return HttpResponseRedirect(reverse('consulting_index'))

        return render_to_response(
                    'consulting/newtreatment_pm.html',
                    {'form': form,
                    'patient_user_id': patient_user_id,
                    'patient_user': patient_user,
                    'treatment_id': treatment_id,
                    'prescriptions': treatment.treatmentprescriptions.all()},
                    context_instance=RequestContext(request))
    return HttpResponseRedirect(reverse('consulting_index'))

# @login_required()
# def add_medications_treatment_pm(request, treatment_id):
#     profile_logged_user = request.user.get_profile()

#     if profile_logged_user.is_doctor():
#         patient_id = request.session['patient_id']
#         user_patient = User.objects.get(id=patient_id)
#         profile_patient = user_patient.get_profile()

#         if request.method == "POST":
#             form = MedicationForm(request.POST)
#             if form.is_valid():
#                 # MEDICINE CAN BE NEW OR ALREADY EXISTED
#                 medicine_name = form.cleaned_data['searcher_medicine']
#                 try:
#                     medicine = Medicine.objects.get(name=medicine_name)
#                     if form.cleaned_data['medicine'].id == -1:
#                         medication = Medication(medicine=medicine,
#                             posology=form.cleaned_data['posology'],
#                             months=form.cleaned_data['months'],
#                             before_after=form.cleaned_data['before_after'])
#                         medication.save()
#                     else:
#                         medication = form.save()
#                 except Medicine.DoesNotExist:
#                     medicine_group = Group.objects.get(id=-1)
#                     medicine = Medicine(name=medicine_name,
#                                         group=medicine_group)
#                     medicine.save()

#                     medication = Medication(medicine=medicine,
#                             posology=form.cleaned_data['posology'],
#                             months=form.cleaned_data['months'],
#                             before_after=form.cleaned_data['before_after'])
#                     medication.save()
#                 # ADD MEDICATION TO TREATMENT
#                 try:
#                     treatment = Treatment.objects.get(id=treatment_id)
#                     treatment.medications.add(medication)
#                     treatment.save()
#                 except Treatment.DoesNotExist:
#                     return HttpResponseRedirect(reverse('consulting_index'))
#                 #INICIALIZE FORM
#                 form = MedicationForm()
#             else:
#                 # ONLY GET TREATMENT OBJECT TO CAN GET ITS MEDICATIONS
#                 try:
#                     treatment = Treatment.objects.get(id=treatment_id)
#                 except Treatment.DoesNotExist:
#                     return HttpResponseRedirect(reverse('consulting_index'))
#         else:
#             form = MedicationForm()

#             try:
#                 treatment = Treatment.objects.get(id=treatment_id)
#             except Treatment.DoesNotExist:
#                 return HttpResponseRedirect(reverse('consulting_index'))

#         return render_to_response(
#                                 'consulting/newtreatment_pm.html',
#                                 {'form': form,
#                                 'profile': profile_patient,
#                                 'patient_id': patient_id,
#                                 'treatment_id': treatment_id,
#                                 'medications': treatment.medications.all()},
#                                 context_instance=RequestContext(request))
#     return HttpResponseRedirect(reverse('consulting_index'))


# @login_required()
# def newtreatment_pm(request):
#     profile = request.user.get_profile()

#     if profile.is_doctor():
#         patient_id = request.session['patient_id']
#         user = User.objects.get(id=patient_id)
#         profile = user.get_profile()

#         if request.method == "POST":
#             form = MedicationForm(request.POST)
#             if form.is_valid():
#                 medicine_id = form.cleaned_data['medicine'].id
#                 # Medicine can be new or not
#                 if medicine_id == -1:
#                     medicine_name = form.cleaned_data['searcher_medicine']
#                     medicine_group = Group.objects.get(id=-1)
#                     medicine = Medicine(name=medicine_name,
#                                         group=medicine_group)
#                     medicine.save()

#                     medication = Medication(medicine=medicine,
#                               posology=form.cleaned_data['posology'],
#                               months=form.cleaned_data['months'],
#                               before_after=form.cleaned_data['before_after'])
#                     medication.save()
#                 else:
#                     medication = form.save()
#                 #Saving treatment is distinct if table is empty or not
#                 # treatment_id = form.cleaned_data['treatment']
#                 treatment_id = request.POST['treatment_id']
#                 if treatment_id:
#                     try:
#                         treatment = Treatment.objects.get(id=treatment_id)
#                         treatment.medications.add(medication)
#                         treatment.save()
#                     except Treatment.DoesNotExist:
#                         return render_to_response(
#                                 'consulting/newtreatment_pm.html',
#                                 {'form': form,
#                                 'profile': profile,
#                                 'patient_id': patient_id},
#                                 context_instance=RequestContext(request))
#                 else:
#                     treatment = Treatment(patient=user,
#                                             from_appointment=False,
#                                             date=datetime.now())
#                     treatment.save()
#                     treatment.medications.add(medication)
#                     treatment.save()
#                     treatment_id = treatment.id

#                 form = MedicationForm()
#                 return render_to_response('consulting/newtreatment_pm.html',
#                                 {'form': form,
#                                 'profile': profile,
#                                 'patient_id': patient_id,
#                                 'treatment_id': treatment_id,
#                                 'medications': treatment.medications.all()},
#                                 context_instance=RequestContext(request))
#             else:
#                 #Saving treatment is distinct if table is empty or not
#                 treatment_id = request.POST['treatment_id']
#                 if treatment_id:
#                     try:
#                         treatment = Treatment.objects.get(id=treatment_id)
#                         medications = treatment.medications.all()
#                         return render_to_response(
#                                     'consulting/newtreatment_pm.html',
#                                     {'form': form,
#                                     'profile': profile,
#                                     'patient_id': patient_id,
#                                     'treatment_id': treatment_id,
#                                     'medications': medications},
#                                     context_instance=RequestContext(request))
#                     except Treatment.DoesNotExist:
#                         return render_to_response(
#                                     'consulting/newtreatment_pm.html',
#                                     {'form': form,
#                                     'profile': profile,
#                                     'patient_id': patient_id},
#                                     context_instance=RequestContext(request))
#                 else:
#                     return render_to_response(
#                                     'consulting/newtreatment_pm.html',
#                                     {'form': form,
#                                     'profile': profile,
#                                     'patient_id': patient_id},
#                                     context_instance=RequestContext(request))
#         else:
#             form = MedicationForm()
#         return render_to_response('consulting/newtreatment_pm.html',
#                                 {'form': form,
#                                 'profile': profile,
#                                 'patient_id': patient_id},
#                                 context_instance=RequestContext(request))
#     return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def remove_prescription_pm(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        if request.method == 'POST':
            prescription_id = request.POST.get("prescription_id", "")
            try:
                prescription = Prescription.objects.get(id=prescription_id)
                prescription.delete()

                treatment_id = request.POST.get("treatment_id", "")
                try:
                    treatment = Treatment.objects.get(id=treatment_id)
                    return render_to_response(
                        'consulting/pharmacological_treatment_pm.html',
                        {'prescriptions':
                                treatment.treatmentprescriptions.all()},
                                context_instance=RequestContext(request))
                except Treatment.DoesNotExist:
                    return HttpResponseRedirect(reverse('consulting_index'))
            except Prescription.DoesNotExist:
                return HttpResponseRedirect(reverse('consulting_index'))

    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@paginate(template_name='consulting/list_treatments_ajax_pm.html',
    list_name='treatments', objects_per_page=settings.OBJECTS_PER_PAGE)
def remove_treatment_pm(request):
    logged_user_profile = request.user.get_profile()
    if logged_user_profile.is_doctor():
        if request.method == 'POST':
            patient_user_id = request.session['patient_user_id']
            patient_user = User.objects.get(id=patient_user_id)
            treatment_id = request.POST.get("treatment_id", "")
            try:
                treatment = Treatment.objects.get(id=treatment_id)
                treatment.delete()

                treatments = Treatment.objects.filter(\
                                patient=patient_user).order_by('-date')

                template_data = {}
                template_data.update({'treatments': treatments})
                return template_data
            except Treatment.DoesNotExist:
                return HttpResponseRedirect(reverse('consulting_index'))
    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def administration(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        return render_to_response('consulting/index_administration.html', {},
                            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def stratification(request):
    logged_user_profile = request.user.get_profile()

    if logged_user_profile.is_doctor():
        return render_to_response('consulting/stratification.html', {},
                            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))
