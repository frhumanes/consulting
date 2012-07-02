#!/usr/bin/python
# -*- encoding: utf-8 -*-
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext_lazy as _
from django.conf import settings
from consulting.models import Appointment


class Profile(models.Model):

    SEX = (
        (-1, _(u'Seleccione el sexo')),
        (1, _(u'Mujer')),
        (2, _(u'Hombre')),
    )
    STATUS = (
        (-1, _(u'Seleccione el estado civil')),
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
    user = models.ForeignKey(User, unique=True)
    doctor = models.ForeignKey(User, blank=True, null=True,
                related_name='doctor')
    patients = models.ManyToManyField(User, blank=True, null=True,
                related_name='patients')
    search_field = models.CharField(_(u'Campo buscador'),
                    max_length=200, blank=True)
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
    sex = models.IntegerField(_(u'Sexo'), choices=SEX, blank=True, null=True)
    address = models.CharField(_(u'Dirección'), max_length=150, blank=True)
    town = models.CharField(_(u'Municipio'), max_length=150, blank=True)
    postcode = models.IntegerField(_(u'Código Postal'), blank=True, null=True)
    dob = models.DateField(_(u'Fecha de Nacimiento'), blank=True, null=True)
    status = models.IntegerField(_(u'Estado Civil'), choices=STATUS,
                                blank=True, null=True)
    phone1 = models.CharField(_(u'Teléfono 1'), max_length=9, blank=True)
    phone2 = models.CharField(_(u'Teléfono 2'), max_length=9, blank=True)
    email = models.EmailField(_(u'Correo Electrónico'), max_length=150,
                                blank=True)
    profession = models.CharField(_(u'Profesión'), max_length=150, blank=True)
    role = models.IntegerField(_(u'Rol'), choices=ROLE, blank=True, null=True)

    def is_doctor(self):
        return self.role == settings.DOCTOR

    def is_administrative(self):
        return self.role == settings.ADMINISTRATIVE

    def is_patient(self):
        return self.role == settings.PATIENT

    def __unicode__(self):
        return u'%s %s %s' % (self.name, self.first_surname,
                                self.second_surname)

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
        appointments = Appointment.objects.filter(
                        patient=self,
                        date__lt=date.today()).order_by(
                        '-date')
        # appointments = Appointment.objects.filter(
        #                 patient=self,
        #                 date_appointment__lt=date.today()).order_by(
        #                 '-date_appointment')

        if appointments.count() > 0:
            # lastAppointment = appointments[0].date_appointment
            lastAppointment = appointments[0].date
        else:
            lastAppointment = ''

        return lastAppointment

    def get_nextAppointment(self):
        # appointments = Appointment.objects.filter(
        #     patient=self, date_appointment__gte=date.today()).order_by(
        #     'date_appointment')
        appointments = Appointment.objects.filter(
            patient=self, date__gte=date.today()).order_by(
            'date')

        if appointments.count() > 0:
            # nextAppointment = appointments[0].date_appointment
            nextAppointment = appointments[0].date
        else:
            nextAppointment = ''

        return nextAppointment
