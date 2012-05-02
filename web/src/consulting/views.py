# -*- encoding: utf-8 -*-
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse
from django.utils import simplejson
from django.contrib.auth.models import User
from userprofile.models import Profile
from userprofile.forms import ProfileForm
from consulting.forms import AppointmentForm
from consulting.models import Appointment
from consulting.helper import strip_accents


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


def newpatient(request):
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


def searcher(request):
    data = {'ok': False}

    if request.method == 'POST':
        start = request.POST.get("start", "")
        profiles = Profile.objects.filter(search_field__icontains=start,
                    role__exact=settings.PATIENT).order_by(
                    'name', 'first_surname', 'second_surname')

        data = {'ok': True,
                'completed_names':
                [{'id': p.id,
                'label':
                (p.name + ' ' + p.first_surname + ' ' + p.second_surname)}\
                 for p in profiles]
                }

    return HttpResponse(simplejson.dumps(data))


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
