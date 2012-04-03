# -*- encoding: utf-8 -*-
from django.conf import settings
from django.template import RequestContext
from django.shortcuts import render_to_response, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect, HttpResponse
from django.utils import simplejson
from django.contrib.auth.models import User
from django.db.models import Q
from userprofile.models import Profile
from userprofile.forms import ProfileForm
from consulting.forms import AppointmentForm
from consulting.models import Appointment
from consulting.helper import strip_accents


@login_required(login_url='/account/login/')
def administrative(request):
    return render_to_response('consulting/administrative.html', {},
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


def newpatient(request):
    exituser = False
    if request.method == "POST":
        form = ProfileForm(request.POST)
        if form.is_valid():
            try:
                nif = form.cleaned_data['nif']
                Profile.objects.get(nif=nif)
                exituser = True
            except Profile.DoesNotExist:
                name = form.cleaned_data['name']
                first_surname = form.cleaned_data['first_surname']
                second_surname = form.cleaned_data['second_surname']
                email = form.cleaned_data['email']

                username = generate_username(strip_accents(name),
                                            strip_accents(first_surname),
                                            nif)

                user = User.objects.create_user(username=username,
                        password=settings.DEFAULT_PASSWORD, email='')
                user.first_name = name
                user.last_name = first_surname + ' ' + second_surname
                user.email = email
                user.save()

                profile = user.get_profile()
                profile.username = username
                profile.name = name
                profile.first_surname = first_surname
                profile.second_surname = second_surname
                profile.nif = nif
                profile.sex = form.cleaned_data['sex']
                profile.address = form.cleaned_data['address']
                profile.town = form.cleaned_data['town']
                profile.postcode = form.cleaned_data['postcode']
                profile.dob = form.cleaned_data['dob']
                profile.status = form.cleaned_data['status']
                profile.phone1 = form.cleaned_data['phone1']
                profile.phone2 = form.cleaned_data['phone2']
                profile.email = email
                profile.profession = form.cleaned_data['profession']
                profile.role = Profile.PATIENT
                profile.save()

                id_newpatient = user.id

                return render_to_response(
                            'consulting/administrative_info_newpatient.html',
                            {'username': username,
                            'id_newpatient': id_newpatient},
                              context_instance=RequestContext(request))

    else:
        form = ProfileForm()

    return render_to_response('consulting/newpatient.html',
                                {'form': form, 'exituser': exituser},
                              context_instance=RequestContext(request))


def newappointment(request, id_newpatient):
    user = get_object_or_404(User, pk=int(id_newpatient))

    if request.method == "POST":
        form = AppointmentForm(request.POST)
        if form.is_valid():
            doctor = form.cleaned_data['doctor']
            profile_patient = user.get_profile()
            profile_patient.doctor = doctor.get_profile()
            profile_patient.save()
            new_appointment = Appointment(patient=user,
                        doctor=form.cleaned_data['doctor'],
                        date=form.cleaned_data['date'],
                        hour=form.cleaned_data['hour'])
            new_appointment.save()
            return HttpResponseRedirect(reverse('administrative_index'))
    else:
        form = AppointmentForm()

    return render_to_response('consulting/newappointment.html',
                                {'name': user.first_name,
                                'surnames': user.last_name,
                                'form': form,
                                'id_newpatient': id_newpatient},
                                context_instance=RequestContext(request))


def appointments_doctor(request):
    if request.method == 'POST':
        id_doctor = request.POST.get("id_doctor", "")
        appointments_doctor = Appointment.objects.filter(doctor=id_doctor)

    return render_to_response('consulting/appointments_doctor.html',
                            {'appointments_doctor': appointments_doctor},
                            context_instance=RequestContext(request))


def searcher(request):
    print 'View searcher'
    start = request.POST.get("start", "")

    # usernames = User.objects.filter(username__startswith=start)

    #  # Object json
    # data = {'usernames': [u.username for u in usernames]}

    profiles = Profile.objects.filter(Q(nif__startswith=start) |
                                    Q(username__startswith=start))
    data = {'usernames': [(p.name + ' ' + p.first_surname + ' ' +
                            p.second_surname) for p in profiles]}

    return HttpResponse(simplejson.dumps(data))
