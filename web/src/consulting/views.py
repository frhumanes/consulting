# -*- encoding: utf-8 -*-
from datetime import datetime
from django.middleware.csrf import get_token
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from decorators import paginate
from userprofile.models import Profile
from userprofile.forms import ProfileForm
from consulting.forms import AppointmentForm, PrescriptionForm
from consulting.models import Appointment, Treatment, Prescription
from consulting.helper import strip_accents
from medicament.models import Component, Group


@login_required()
def index(request):

    profile = request.user.get_profile()

    if profile.role == settings.DOCTOR:
        return render_to_response('consulting/index_doctor.html', {},
                                context_instance=RequestContext(request))
    elif profile.role == settings.ADMINISTRATIVE:
        return render_to_response('consulting/index_administrative.html', {},
                                context_instance=RequestContext(request))
    else:
        #profile.role == settings.PATIENT
        return render_to_response('consulting/index_patient.html', {},
                                context_instance=RequestContext(request))


def generate_username(name, first_surname, nif):

    LEN_NIF = -3
    split_name = name.lower().split()
    first_letter = split_name[0][0]
    second_letter = ''

    if len(split_name) > 1:
        last_position = len(split_name) - 1
        second_letter = split_name[last_position][0]

    sub_nif = nif[LEN_NIF:]

    username = first_letter + second_letter + first_surname.lower() + sub_nif

    return username


# REPASAR or profile.is_administrative()
@login_required()
def newpatient(request):
    profile = request.user.get_profile()

    if profile.is_doctor() or profile.is_administrative():
        exist_user = False
        same_username = False

        if request.method == "POST":
            form = ProfileForm(request.POST)
            if form.is_valid():
                try:
                    nif = form.cleaned_data['nif']
                    Profile.objects.get(nif=nif)
                    exist_user = True
                except Profile.DoesNotExist:
                    name = form.cleaned_data['name']
                    first_surname = form.cleaned_data['first_surname']
                    second_surname = form.cleaned_data['second_surname']
                    email = form.cleaned_data['email']

                    username = generate_username(strip_accents(name),
                                                strip_accents(first_surname),
                                                strip_accents(nif))
                    try:
                        Profile.objects.get(username=username)
                        same_username = True

                    except Profile.DoesNotExist:
                        user = User.objects.create_user(username=username,
                            password=settings.DEFAULT_PASSWORD, email=email)
                        user.first_name = name
                        user.last_name = first_surname + ' ' + second_surname
                        user.email = email
                        user.profile = create_or_update_profile(user,
                            form, username, settings.PATIENT)
                        user.save()

                        id_newpatient = user.id

                        return render_to_response(
                            'consulting/newpatient_info.html',
                            {'username': username,
                            'id_newpatient': id_newpatient},
                            context_instance=RequestContext(request))
        else:
            form = ProfileForm()

        return render_to_response('consulting/newpatient.html',
                                    {'form': form, 'exist_user': exist_user,
                                    'same_username': same_username},
                                    context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('main_index'))


def create_or_update_profile(user, form, username, role):
    name = form.cleaned_data['name']
    first_surname = form.cleaned_data['first_surname']
    second_surname = form.cleaned_data['second_surname']
    nif = form.cleaned_data['nif']

    profile = Profile()
    profile.user = user
    profile.search_field = name + ' ' + first_surname + ' ' +\
                            second_surname + ' ' + nif
    profile.username = username
    profile.name = name
    profile.first_surname = first_surname
    profile.second_surname = second_surname
    profile.nif = nif
    profile.email = form.cleaned_data['email']
    profile.sex = form.cleaned_data['sex']
    profile.address = form.cleaned_data['address']
    profile.town = form.cleaned_data['town']
    profile.postcode = form.cleaned_data['postcode']
    profile.dob = form.cleaned_data['dob']
    profile.status = form.cleaned_data['status']
    profile.phone1 = form.cleaned_data['phone1']
    profile.phone2 = form.cleaned_data['phone2']
    profile.profession = form.cleaned_data['profession']
    profile.role = role

    profile.save()


def newappointment(request, id_newpatient):
    patient_user = get_object_or_404(User, pk=int(id_newpatient))
    patientfullname = patient_user.first_name + ' ' + patient_user.last_name

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            #UPDATE PROFILE DOCTOR
            doctor_user = form.cleaned_data['doctor']
            profile_doctor = doctor_user.get_profile()
            profile_doctor.patients.add(patient_user)
            profile_doctor.save()

            #UPDATE PROFILE PATIENT
            #IF IT'S FIRST APPOINTMENT OF PATIENT
            if Appointment.objects.filter(patient=id_newpatient).count() == 0:
                profile_patient = patient_user.get_profile()
                profile_patient.doctor = doctor_user
                profile_patient.save()

            form.save()

            return render_to_response('consulting/index_administrative.html',
                            {},
                            context_instance=RequestContext(request))
    else:
        form = AppointmentForm(initial={'patient': patient_user})

    return render_to_response('consulting/newappointment.html',
                                {'patientfullname': patientfullname,
                                'form': form,
                                'id_newpatient': id_newpatient},
                                context_instance=RequestContext(request))


# REPASAR
def appointments_doctor(request):
    if request.method == 'POST':
        id_doctor = request.POST.get("id_doctor", "")
        appointments_doctor = Appointment.objects.filter(doctor=id_doctor)

    return render_to_response('consulting/appointments_doctor.html',
                            {'appointments_doctor': appointments_doctor},
                            context_instance=RequestContext(request))


@login_required()
def searcher(request):
    profile = request.user.get_profile()

    if profile.is_doctor:
        data = {'ok': False}

        if request.method == 'POST':
            start = request.POST.get("start", "")
            profiles = Profile.objects.filter(search_field__icontains=start,
                        role__exact=settings.PATIENT)
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
    profile = request.user.get_profile()

    if profile.is_doctor():
        data = {'ok': False}

        if request.method == 'POST':
            kind_component = request.POST.get("kind_component", "")
            start = request.POST.get("start", "").lower()

            if int(kind_component) == settings.ACTIVE_INGREDIENT:
                components = Component.objects.filter(
                Q(kind_component__exact=settings.ACTIVE_INGREDIENT),
                Q(name__icontains=start) | Q(groups__name__icontains=start))\
                .distinct()
            else:
                #settings.MEDICINE
                components = Component.objects.filter(
                Q(kind_component__exact=settings.MEDICINE),
                Q(name__icontains=start) | Q(groups__name__icontains=start))\
                .distinct()

            data = {'ok': True,
                    'components':
                        [{'id': c.id, 'label': (c.name)} for c in components]}
            # medicines = Medicine.objects.filter(Q(name__icontains=start) | \
            #                   Q(group__name__icontains=start) | \
            #                   Q(active_ingredients__name__icontains=start)).\
            #                     distinct()
            ####### PRIMERA VERSION #######
            # data = {'ok': True,
            #         'medicines':
            #             [{'id': m.id, 'label': (m.name)} for m in medicines],
            #         'lenght': medicines.count()
            #         }

            ####### SEGUNDA VERSION #######
            # data = {'ok': True,
            #         'medicines':
            #[{'id': m.id, 'label': (m.group.name + '-' + m.name)}
            # for m in medicines],
            #         'lenght': medicines.count()
            #         }
            ####### TERCERA VERSION #######
            # elto = {}
            # medicines_list = []

            # for m in medicines:
            #     str_label = ""
            #     str_label = str_label + m.name + ': '
            #     for ai in m.active_ingredients.all():
            #         str_label = str_label + ai.name + '+'

            #     elto = {'id': m.id, 'label': str_label}

            #     medicines_list.append(elto)

            # data = {'ok': True,
            #         'medicines': medicines_list,
            #         'lenght': medicines.count()
            #         }

            ####### CUARTA VERSION #######
            # active_ingredients = ActiveIngredient.objects.
            #filter(name__icontains=start).order_by('name')

            # data = {'ok': True,
            #         'medicines':
            #             [{'id': ai.id, 'label': ai.name}
            #for ai in active_ingredients]
            #         }

        return HttpResponse(simplejson.dumps(data))
    return HttpResponseRedirect(reverse('consulting_index'))


#CAMBIAR: COINCIDENCIAS SOLO EN PROFILE DEL USUARIO LOGADO
# def searcher_doctor_patients(request):
#     data = {'ok': False}

#     if request.method == 'POST':
#         start = request.POST.get("start", "")
#         profiles = Profile.objects.filter(search_field__icontains=start,
#                     role__exact=settings.PATIENT).order_by(
#                     'name', 'first_surname', 'second_surname')

#         data = {'ok': True,
#                 'completed_names':
#                 [{'id': p.id,
#                 'label':
#                 (p.name + ' ' + p.first_surname + ' ' + p.second_surname)}\
#                  for p in profiles]
#                 }

#     return HttpResponse(simplejson.dumps(data))


def patient_appointments(request):
    if request.method == 'POST':
        patient_id = request.POST.get("patient_id", "")
        profile = Profile.objects.get(id=patient_id)

        patient_appointments = Appointment.objects.filter(patient=patient_id)

        return render_to_response('consulting/list_appointments_patient.html',
                            {'patient_appointments': patient_appointments,
                            'profile': profile},
                            context_instance=RequestContext(request))

    return render_to_response('consulting/index_administrative.html', {},
                                context_instance=RequestContext(request))


@login_required()
def patient_management(request):
    profile = request.user.get_profile()

    if profile.is_doctor():
        return render_to_response('consulting/index_pm.html', {},
                            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def personal_data_pm(request, patient_id):
    profile = request.user.get_profile()

    if profile.is_doctor():
        # IMPORTANT! patient_id is user_id of patient
        request.session['patient_id'] = patient_id
        user = User.objects.get(id=patient_id)
        profile = user.get_profile()
        return render_to_response('consulting/personal_data_pm.html',
                        {'profile': profile,
                        'patient_id': patient_id},
                        context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
@paginate(template_name='consulting/list_treatments_pm.html',
    list_name='treatments', objects_per_page=settings.OBJECTS_PER_PAGE)
def list_treatments_pm(request):
    profile = request.user.get_profile()

    if profile.is_doctor():
        patient_id = request.session['patient_id']
        patient_user = User.objects.get(id=patient_id)
        patient_profile = patient_user.get_profile()

        treatments = Treatment.objects.filter(patient=patient_user).\
                                                order_by('-date')

        template_data = {}
        template_data.update({'profile': patient_profile,
                                'treatments': treatments,
                                'patient_id': patient_id,
                                'csrf_token': get_token(request)})
        return template_data
    else:
        return HttpResponseRedirect(reverse('consulting_index'))


# @login_required()
# def list_treatments_pm(request):
#     profile = request.user.get_profile()

#     if profile.is_doctor():
#         patient_id = request.session['patient_id']
#         patient_user = User.objects.get(id=patient_id)
#         patient_profile = patient_user.get_profile()

#         treatments = Treatment.objects.filter(patient=patient_user)

#         return render_to_response('doctor/list_treatments.html',
#                         {'profile': patient_profile,
#                         'treatments': treatments,
#                         'csrf_token': get_token(request)},
#                         context_instance=RequestContext(request))
#     else:
#         return HttpResponseRedirect(reverse('main_index'))


@login_required()
def detail_treatment_pm(request):
    profile = request.user.get_profile()

    if profile.is_doctor():
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
    profile_logged_user = request.user.get_profile()

    if profile_logged_user.is_doctor():
        patient_id = request.session['patient_id']
        user_patient = User.objects.get(id=patient_id)

        treatment = Treatment(patient=user_patient,
                                from_appointment=False,
                                date=datetime.now())
        treatment.save()

        return HttpResponseRedirect(
            reverse('consulting_add_prescriptions_treatment_pm',
            args=[treatment.id]))

    return HttpResponseRedirect(reverse('consulting_index'))


@login_required()
def add_prescriptions_treatment_pm(request, treatment_id):
    profile_logged_user = request.user.get_profile()

    if profile_logged_user.is_doctor():
        patient_id = request.session['patient_id']
        user_patient = User.objects.get(id=patient_id)
        profile_patient = user_patient.get_profile()

        if request.method == "POST":
            try:
                treatment = Treatment.objects.get(id=treatment_id)
                form = PrescriptionForm(request.POST)
                if form.is_valid():
                    # MEDICINE CAN BE NEW OR ALREADY EXISTED
                    component_name = form.cleaned_data['searcher_component']
                    try:
                        component = Component.objects.get(name=component_name)
                        prescription = form.save(commit=False)
                        prescription.treatment = treatment
                        prescription.component = component
                        prescription.save()
                    except Component.DoesNotExist:
                        kind_component = form.cleaned_data['kind_component']
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
                    'profile': profile_patient,
                    'patient_id': patient_id,
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
    profile = request.user.get_profile()

    if profile.is_doctor():
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
    profile = request.user.get_profile()
    if profile.is_doctor():
        if request.method == 'POST':
            patient_id = request.session['patient_id']
            patient_user = User.objects.get(id=patient_id)
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
