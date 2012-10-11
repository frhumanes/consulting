# -*- encoding: utf-8 -*-
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from log.models import TraceableModel
from illness.models import Illness
from cal.models import Appointment
from consulting.models import Task, Conclusion, Medicine
from private_messages.models import Message
from datetime import date, timedelta, datetime


class Profile(TraceableModel):

    SEX = (
        (-1, ''),
        (1, _(u'Mujer')),
        (2, _(u'Hombre')),
    )
    STATUS = (
        (-1, ''),
        (settings.MARRIED, _(u'Casado')),
        (settings.STABLE_PARTNER, _(u'Pareja Estable')),
        (settings.DIVORCED, _(u'Divorciado')),
        (settings.WIDOW_ER, _(u'Viudo/a')),
        (settings.SINGLE, _(u'Soltero/a')),
        (settings.OTHER, _(u'Otro')),
    )

    ROLE = (
        (settings.DOCTOR, _(u'Médico')),
        (settings.ADMINISTRATIVE, _(u'Administrativo')),
        (settings.PATIENT, _(u'Paciente')),
    )
    #username is the nick with you login in app
    user = models.ForeignKey(User, unique=True, related_name='profiles')
    doctor = models.ForeignKey(User, blank=True, null=True,
                                related_name='doctor')
    patients = models.ManyToManyField(User, related_name='patients_profiles',
                                        blank=True, null=True)

    illnesses = models.ManyToManyField(Illness,
                                    related_name='illnesses_profiles',
                                    blank=True, null=True)

    username = models.CharField(_(u'Nombre de usuario'), max_length=50,
                                blank=True)

    name = models.CharField(_(u'Nombre'), max_length=150, blank=True)

    first_surname = models.CharField(_(u'Primer Apellido'), max_length=150,
                                    blank=True)

    second_surname = models.CharField(_(u'Segundo Apellido'), max_length=150,
                                        blank=True)

    nif = models.CharField(_(u'NIF'), max_length=9, null=True, unique=True)

    def unique_error_message(self, model_class, unique_check):
        if unique_check == ("nif",):
            return _(u'Ya existe un Paciente con este NIF')
        else:
            return super(Profile, self).unique_error_message(
                                                model_class, unique_check)

    sex = models.IntegerField(_(u'Sexo'), choices=SEX,
                            default=SEX[0][0], blank=True, null=True)

    address = models.CharField(_(u'Dirección'), max_length=150, blank=True)

    town = models.CharField(_(u'Municipio'), max_length=150, blank=True)

    postcode = models.IntegerField(_(u'Código Postal'), blank=True, null=True)

    dob = models.DateField(_(u'Fecha de Nacimiento'), blank=True, null=True)

    status = models.IntegerField(_(u'Estado Civil'), choices=STATUS,
                                default=STATUS[0][0], blank=True, null=True)

    phone1 = models.CharField(_(u'Teléfono 1'), max_length=9, blank=True)

    phone2 = models.CharField(_(u'Teléfono 2'), max_length=9, blank=True)

    email = models.EmailField(_(u'Correo Electrónico'), max_length=150,
                                blank=True)

    profession = models.CharField(_(u'Profesión'), max_length=150, blank=True)

    role = models.IntegerField(_(u'Rol'), choices=ROLE, blank=True, null=True)

    def get_full_name(self):
        return "%s %s %s" % (self.name, self.first_surname, self.second_surname)

    def is_doctor(self):
        return self.role == settings.DOCTOR

    def is_administrative(self):
        return self.role == settings.ADMINISTRATIVE

    def is_patient(self):
        return self.role == settings.PATIENT

    def __unicode__(self):
        return u'id: %s profile: %s %s %s' \
            % (self.id, self.name, self.first_surname, self.second_surname)

    def age(self, dob):
        today = date.today()
        years = today.year - dob.year
        if today.month < dob.month or\
            today.month == dob.month and today.day < dob.day:
            years -= 1
        return years

    def get_age(self):
        if not self.dob is None:
            return self.age(self.dob)
        else:
            return ''

    def get_sex(self):
        if self.sex == settings.WOMAN:
            return _(u'Mujer')
        elif self.sex == settings.MAN:
            return _(u'Hombre')
        else:
            return ''

    def get_status(self):
        if self.status == settings.MARRIED:
            if self.sex == settings.WOMAN:
                status = _(u'Casada')
            else:
                status = _(u'Casado')
        elif self.status == settings.STABLE_PARTNER:
            status = _(u'Pareja Estable')
        elif self.status == settings.DIVORCED:
            if self.sex == settings.WOMAN:
                status = _(u'Divorciada')
            else:
                status = _(u'Divorciado')
        elif self.status == settings.WIDOW_ER:
            if self.sex == settings.WOMAN:
                status = _(u'Viuda')
            else:
                status = _(u'Viudo')
        elif self.status == settings.SINGLE:
            if self.sex == settings.WOMAN:
                status = _(u'Soltera')
            else:
                status = _(u'Soltero')
        else:
            status = _(u'Otro')

        return status

    def get_lastAppointment(self):
        appointments = Appointment.objects.filter(patient=self.user,
                        date__lt=date.today()).order_by(
                        '-date')

        if appointments.count() > 0:
            lastAppointment = appointments[0]
        else:
            lastAppointment = ''

        return lastAppointment

    def get_nextAppointment(self):
        appointments = Appointment.objects.filter(patient=self.user,
                            date__gte=date.today()).order_by(
                            'date')

        if appointments.count() > 0:
            nextAppointment = appointments[0]
        else:
            nextAppointment = ''

        return nextAppointment

    def get_conclusions(self):
        return Conclusion.objects.filter(patient=self.user).latest('date')

    def get_treatment(self):
        return Medicine.objects.filter(patient=self.user,date__isnull=True).order_by('component')

    def get_pending_tasks(self):
        next_app = self.get_nextAppointment()
        tasks = []
        if next_app and next_app.date >= date.today():
            ddays = (next_app.date-date.today()).days
            tasks = Task.objects.filter(patient=self.user,
                                        self_administered=True, 
                                        completed=False,
                                        assess=True,
                                        previous_days__gte=ddays).order_by('-creation_date')
        return tasks


    def get_anxiety_status(self):
        try:
            latest_task = Task.objects.filter(patient=self.user, survey__id__in=(settings.INITIAL_ASSESSMENT, settings.ANXIETY_DEPRESSION_SURVEY), completed=True).latest('end_date')
            return latest_task.get_anxiety_status()
        except:
            pass

    def get_depression_status(self):
        try:
            latest_task = Task.objects.filter(patient=self.user, survey__id__in=(settings.INITIAL_ASSESSMENT, settings.ANXIETY_DEPRESSION_SURVEY), completed=True).latest('end_date')
            return latest_task.get_depression_status()
        except:
            pass

    def get_unread_messages(self):
        return Message.objects.get_pending_for_user(self.user)
