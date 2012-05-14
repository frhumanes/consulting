# -*- encoding: utf-8 -*-
from datetime import datetime
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.utils import simplejson
from django.db.models import Q
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from userprofile.models import Profile
from userprofile.forms import ProfileForm
from consulting.forms import AppointmentForm, MedicationForm
from consulting.models import Appointment, Treatment, Medication
from consulting.helper import strip_accents
from medicament.models import Medicine, Group


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
                            'administrative/newpatient_info.html',
                            {'username': username,
                            'id_newpatient': id_newpatient},
                            context_instance=RequestContext(request))
        else:
            form = ProfileForm()

        return render_to_response('administrative/newpatient.html',
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

            return render_to_response('administrative/index.html', {},
                            context_instance=RequestContext(request))
    else:
        form = AppointmentForm(initial={'patient': patient_user})

    return render_to_response('administrative/newappointment.html',
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
    return HttpResponseRedirect(reverse('main_index'))


@login_required()
def searcher_medicine(request):
    profile = request.user.get_profile()

    if profile.is_doctor():
        data = {'ok': False}

        if request.method == 'POST':
            start = request.POST.get("start", "").lower()
            medicines = Medicine.objects.filter(Q(name__icontains=start) | \
                                Q(group__name__icontains=start) | \
                                Q(active_ingredients__name__icontains=start)).\
                                distinct()

            data = {'ok': True,
                    'medicines':
                        [{'id': m.id, 'label': (m.name)} for m in medicines],
                    'lenght': medicines.count()
                    }

        return HttpResponse(simplejson.dumps(data))
    return HttpResponseRedirect(reverse('main_index'))


def details_medicine_pm(request, medicine_id):
    medicine = Medicine.objects.get(id=medicine_id)
    return render_to_response('doctor/aux_pm.html',
                    {'medicine': medicine},
                    context_instance=RequestContext(request))

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

        return render_to_response('patient/list_appointments.html',
                            {'patient_appointments': patient_appointments,
                            'profile': profile},
                            context_instance=RequestContext(request))

    return render_to_response('administrative/index.html', {},
                                context_instance=RequestContext(request))


@login_required()
def patient_management(request):
    profile = request.user.get_profile()

    if profile.is_doctor():
        return render_to_response('doctor/index_pm.html', {},
                            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('main_index'))


@login_required()
def personal_data_pm(request, patient_id):
    profile = request.user.get_profile()

    if profile.is_doctor():
        # IMPORTANT! patient_id is user_id of patient
        request.session['patient_id'] = patient_id
        user = User.objects.get(id=patient_id)
        profile = user.get_profile()

        return render_to_response('doctor/personal_data_pm.html',
                        {'profile': profile},
                        context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(reverse('main_index'))


@login_required()
def newtreatment_pm(request):
    profile = request.user.get_profile()

    if profile.is_doctor():
        patient_id = request.session['patient_id']
        user = User.objects.get(id=patient_id)
        profile = user.get_profile()

        if request.method == "POST":
            form = MedicationForm(request.POST)
            if form.is_valid():
                medicine_id = form.cleaned_data['medicine'].id
                # Medicine can be new or not
                if medicine_id == -1:
                    medicine_name = form.cleaned_data['searcher_medicine']
                    medicine_group = Group.objects.get(id=-1)
                    medicine = Medicine(name=medicine_name,
                                        group=medicine_group)
                    medicine.save()

                    medication = Medication(medicine=medicine,
                                posology=form.cleaned_data['posology'],
                                time=form.cleaned_data['time'],
                                before_after=form.cleaned_data['before_after'])
                    medication.save()
                else:
                    medication = form.save()
                #Saving treatment is distinct if table is empty or not
                treatment_id = form.cleaned_data['treatment']
                if treatment_id:
                    try:
                        treatment = Treatment.objects.get(id=treatment_id)
                        treatment.medications.add(medication)
                    except Treatment.DoesNotExist:
                        return render_to_response(
                                'doctor/newtreatment_pm.html',
                                {'form': form,
                                'profile': profile},
                                context_instance=RequestContext(request))
                else:
                    treatment = Treatment(patient=user,
                                            from_appointment=False,
                                            date=datetime.now())
                    treatment.save()
                    treatment.medications.add(medication)
                    treatment.save()
                    treatment_id = treatment.id

                form = MedicationForm(initial={'treatment': treatment_id})
                return render_to_response('doctor/newtreatment_pm.html',
                                {'form': form,
                                'profile': profile,
                                'treatment_id': treatment_id,
                                'medications': treatment.medications.all()},
                                context_instance=RequestContext(request))
            else:
                #Saving treatment is distinct if table is empty or not
                treatment_id = request.POST['treatment']
                if treatment_id:
                    try:
                        treatment = Treatment.objects.get(id=treatment_id)
                        medications = treatment.medications.all()
                        return render_to_response(
                                    'doctor/newtreatment_pm.html',
                                    {'form': form,
                                    'profile': profile,
                                    'treatment_id': treatment_id,
                                    'medications': medications},
                                    context_instance=RequestContext(request))
                    except Treatment.DoesNotExist:
                        return render_to_response(
                                    'doctor/newtreatment_pm.html',
                                    {'form': form,
                                    'profile': profile},
                                    context_instance=RequestContext(request))
                else:
                    return render_to_response(
                                    'doctor/newtreatment_pm.html',
                                    {'form': form,
                                    'profile': profile},
                                    context_instance=RequestContext(request))
        else:
            form = MedicationForm()
        return render_to_response('doctor/newtreatment_pm.html',
                                {'form': form, 'profile': profile},
                                context_instance=RequestContext(request))
    return HttpResponseRedirect(reverse('main_index'))


@login_required()
def remove_medication(request):
    profile = request.user.get_profile()

    if profile.is_doctor():
        if request.method == 'POST':
            medication_id = request.POST.get("medication_id", "")
            try:
                medication = Medication.objects.get(id=medication_id)
                medication.delete()

                treatment_id = request.POST.get("treatment_id", "")
                try:
                    treatment = Treatment.objects.get(id=treatment_id)
                    medications = treatment.medications.all()
                    return render_to_response(
                                    'doctor/pharmacological_treatment.html',
                                    {'medications': medications},
                                    context_instance=RequestContext(request))
                except Treatment.DoesNotExist:
                    return HttpResponseRedirect(reverse('main_index'))
            except Medication.DoesNotExist:
                return HttpResponseRedirect(reverse('main_index'))

    return HttpResponseRedirect(reverse('main_index'))
