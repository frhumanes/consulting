# -*- encoding: utf-8 -*-
from datetime import date
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.conf import settings
from django.db.models import Q

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
        (settings.MARRIED, _(u'Casado/a')),
        (settings.STABLE_PARTNER, _(u'Pareja Estable')),
        (settings.DIVORCED, _(u'Divorciado/a')),
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
    user = models.ForeignKey(User, unique=True, related_name='profiles',
                            help_text='Usuario asociado del sistema')
    doctor = models.ForeignKey(User, blank=True, null=True,
                                related_name='doctor', limit_choices_to = {'profiles__role':settings.DOCTOR})
    #patients = models.ManyToManyField(User, related_name='patients_profiles',
    #                                    blank=True, null=True)

    illnesses = models.ManyToManyField(Illness,
                                    related_name='illnesses_profiles',
                                    blank=True, null=True)

    name = models.CharField(_(u'Nombre'), max_length=150, blank=True)

    first_surname = models.CharField(_(u'Primer Apellido'), max_length=150,
                                    blank=True)

    second_surname = models.CharField(_(u'Segundo Apellido'), max_length=150,
                                        blank=True, default='')

    nif = models.CharField(_(u'DNI/NIF'), max_length=9, null=True, unique=True,
        help_text=_(u"Requerido para pacientes mayores de 14 años"))

    def unique_error_message(self, model_class, unique_check):
        if unique_check == ("nif",):
            return _(u'Ya existe un Paciente con este DNI/NIF')
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
                                null=True, unique=True, blank=True)

    profession = models.CharField(_(u'Profesión'), max_length=150, blank=True)

    role = models.IntegerField(_(u'Rol'), choices=ROLE, blank=True, null=True)

    updated_password_at = models.DateTimeField(_(u'Última vez que actualizó la contraseña'), auto_now_add=True)

    def save(self, *args, **kw):
        if self.email == '':
            self.email = None
        if self.nif == '':
            self.nif = None
        super(Profile, self).save(*args, **kw)

    def get_full_name(self, title=False):
        if title:
            pre = ''
            if self.role == settings.DOCTOR:
                if self.sex == settings.WOMAN:
                    pre = u'Dra.'
                elif self.sex == settings.MAN:
                    pre = u'Dr.'
            else:
                if self.sex == settings.MAN:
                    pre = u'D.'
                elif self.sex == settings.WOMAN:
                    pre = u'D.ª'
            return u"%s %s %s %s" % (pre, self.name, self.first_surname, self.second_surname)
        return u"%s %s %s" % (self.name, self.first_surname, self.second_surname)

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

    def get_next_real_appointment(self):
        appointments = Appointment.objects.filter(
                            Q(patient=self.user, notify=True, status=settings.CONFIRMED),
                            Q(date__gt=date.today()) |
                            Q(date=date.today(), start_time__gte=datetime.time(datetime.now()))).order_by(
                            'date')

        for app in appointments:
            if not app.has_activity():
                nextAppointment = app
                break
        else:
            nextAppointment = ''

        return nextAppointment

    def get_nextAppointment(self):
        appointments = Appointment.objects.filter(
                            Q(patient=self.user),
                            Q(date__gt=date.today()) |
                            Q(date=date.today(), 
                              start_time__gte=datetime.time(datetime.now()))
                            ).exclude(status__in=[settings.CANCELED_BY_PATIENT,
                                                 settings.CANCELED_BY_DOCTOR]
                            ).order_by('date')

        for app in appointments:
            if not app.has_activity():
                nextAppointment = app
                break
        else:
            nextAppointment = ''

        return nextAppointment

    def get_conclusions(self):
        return Conclusion.objects.filter(appointment__patient=self.user).latest('date')

    def get_treatment(self, at_date=None):
        if at_date:
            return Medicine.objects.filter(Q(patient=self.user,
                                             created_at__lte=at_date,
                                             is_previous=False),
                                           Q(date__isnull=True) |
                                           Q(date__gte=at_date)).order_by('id')
        else:
            return Medicine.objects.filter(patient=self.user,date__isnull=True, is_previous=False).order_by('component')

    def get_pending_tasks(self):
        next_app = self.get_nextAppointment()
        tasks = []
        if next_app and datetime.combine(next_app.date, next_app.start_time) >= datetime.now():
            ddays = (next_app.date-date.today()).days
            tasks = Task.objects.filter(patient=self.user,
                                        self_administered=True, 
                                        completed=False,
                                        assess=True,
                                        previous_days__gte=ddays,
                                        previous_days__gt=0).order_by('-creation_date')
        return tasks


    def get_anxiety_status(self, at_date=None, index=False, html=False):
        filter_option = Q(patient=self.user, survey__code__in=(settings.INITIAL_ASSESSMENT, settings.ANXIETY_DEPRESSION_SURVEY), completed=True, assess=False)
        if at_date:
            filter_option = filter_option & Q(end_date__lte=at_date)
        try:
            for task in Task.objects.filter(filter_option).order_by('-end_date'):
                status = task.get_anxiety_status(index)
                if status != '':
                    break
            if html:
                if status[0]  != ' ':
                    return '<span style="min-width:100px" class="label label-%s" >%s</span>' % (status[1], status[0])
                return ''
            else:
                return status
        except:
            return ''

    def get_depression_status(self, at_date=None, index=False, html=False):
        filter_option = Q(patient=self.user, survey__code__in=(settings.INITIAL_ASSESSMENT, settings.ANXIETY_DEPRESSION_SURVEY), completed=True, assess=False)
        if at_date:
            filter_option = filter_option & Q(end_date__lte=at_date)
        try:
            for task in Task.objects.filter(filter_option).order_by('-end_date'):
                status = task.get_depression_status(index)
                if status != '':
                    break
            if html:
                if status[0] != ' ':
                    return '<span style="min-width:100px" class="label label-%s" >%s</span>' % (status[1], status[0])
                return ''
            else:
                return status
        except:
            return ''


    def get_unread_messages(self):
        return Message.objects.get_pending_for_user(self.user)

    def get_mobile_phone(self):
        if self.phone1 and int(self.phone1)/int(10e7) in (6, 7):
            return self.phone1
        elif self.phone2 and int(self.phone2)/int(10e7) in (6, 7):
            return self.phone2
        else:
            return None

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"
        ordering = ['first_surname', 'second_surname', 'name', 'id']