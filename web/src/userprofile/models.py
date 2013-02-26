# -*- encoding: utf-8 -*-
from datetime import date
from datetime import datetime
from datetime import time
from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.conf import settings
from django.db.models import Q

from math import floor

from log.models import TraceableModel
from illness.models import Illness
from cal.models import Appointment
from consulting.models import Task, Conclusion, Medicine
from private_messages.models import Message
from survey.models import Block


class Profile(TraceableModel):

    SEX = (
        (1, _(u'Mujer')),
        (2, _(u'Hombre')),
    )
    STATUS = (
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

    EDUCATION = (
        (1, _(u'Analfabeto por problemas físicos o psíquicos')),
        (2, _(u'Analfabeto por otras razones')),
        (3, _(u'Sin estudios')),
        (4, _(u'Estudios primarios o equivalentes')),
        (5, _(u'Enseñanza general secundaria, 1er ciclo')),
        (6, _(u'Enseñanza Profesional de 2º grado, 2º ciclo')),
        (7, _(u'Enseñanza general secundaria, 2º ciclo')),
        (8, _(u'Enseñanzas profesionales superiores')),
        (9, _(u'Estudios universitarios o equivalentes'))
    )
    #username is the nick with you login in app
    user = models.ForeignKey(User, unique=True, related_name='profiles',
                             help_text='Usuario asociado del sistema')
    doctor = models.ForeignKey(User, blank=True, null=True,
                               related_name='doctor',
                               limit_choices_to={
                               'profiles__role': settings.DOCTOR
                               })
    #patients = models.ManyToManyField(User, related_name='patients_profiles',
    #                                    blank=True, null=True)
    medical_number = models.CharField(_(u'Historia médica'),
                                      max_length=9,
                                      unique=True,
                                      null=True,
                                      blank=True)

    illnesses = models.ManyToManyField(
        Illness,
        related_name='illnesses_profiles',
        blank=True,
        null=True,
        limit_choices_to={'cie_code__isnull': True, 'parent__isnull': False}
    )

    name = models.CharField(_(u'Nombre'), max_length=150, blank=True)

    first_surname = models.CharField(_(u'Primer Apellido'), max_length=150,
                                     blank=True)

    second_surname = models.CharField(_(u'Segundo Apellido'), max_length=150,
                                      blank=True, default='')

    nif = models.CharField(
        _(u'DNI/NIF'),
        max_length=9,
        null=True,
        unique=True,
        help_text=_(u"Requerido para pacientes mayores de 14 años")
    )

    def unique_error_message(self, model_class, unique_check):
        if unique_check == ("nif",):
            return _(u'Ya existe un Paciente con este DNI/NIF')
        else:
            return super(Profile, self).unique_error_message(model_class,
                                                             unique_check)

    sex = models.IntegerField(_(u'Sexo'), choices=SEX,
                              blank=True, null=True)

    address = models.CharField(_(u'Dirección'), max_length=150, blank=True)

    town = models.CharField(_(u'Municipio'), max_length=150, blank=True)

    postcode = models.IntegerField(_(u'Código Postal'), blank=True, null=True)

    dob = models.DateField(_(u'Fecha de Nacimiento'), blank=True, null=True)

    status = models.IntegerField(_(u'Estado Civil'), choices=STATUS,
                                 default=STATUS[0][0], blank=True, null=True)

    phone1 = models.CharField(_(u'Teléfono 1'), max_length=9, blank=True)

    phone2 = models.CharField(_(u'Teléfono 2'), max_length=9, blank=True)

    emergency_phone = models.CharField(
        _(u'En caso de emergencia avisar a'),
        max_length=500,
        blank=True
    )

    email = models.EmailField(_(u'Correo Electrónico'), max_length=150,
                              null=True, unique=True, blank=True)

    education = models.IntegerField(_(u'Nivel de estudios'), choices=EDUCATION,
                                    blank=True, null=True)

    profession = models.CharField(_(u'Profesión'), max_length=150, blank=True)

    source = models.CharField(_(u'Fuente de derivación'), max_length=255,
                              blank=True)

    role = models.IntegerField(_(u'Rol'), choices=ROLE, blank=True, null=True)

    updated_password_at = models.DateTimeField(
        _(u'Última vez que actualizó la contraseña'),
        auto_now_add=True
    )

    def save(self, *args, **kw):
        if self.email == '':
            self.email = None
        if self.nif == '':
            self.nif = None
        if not self.sex:
            self.sex = None
        if self.medical_number == '':
            self.medical_number = None
        super(Profile, self).save(*args, **kw)
        if not self.user.is_active:
            for app in Appointment.objects.filter(
                Q(patient=self.user),
                Q(date__gt=date.today()) |
                Q(date=date.today(),
                  start_time__gte=datetime.time(datetime.now()))
            ).exclude(
                status__in=[settings.CANCELED_BY_PATIENT,
                            settings.CANCELED_BY_DOCTOR]).order_by('date'):
                app.status = settings.CANCELED_BY_DOCTOR
                app.save()
        if not self.medical_number and self.role == settings.PATIENT:
            self.medical_number = "%s%05d" % (date.today().year, self.pk)
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
            return u"%s %s %s %s" % (pre, self.name,
                                     self.first_surname,
                                     self.second_surname)
        return u"%s %s %s" % (self.name,
                              self.first_surname,
                              self.second_surname)

    def is_doctor(self):
        return self.role == settings.DOCTOR

    def is_administrative(self):
        return self.role == settings.ADMINISTRATIVE

    def is_patient(self):
        return self.role == settings.PATIENT

    def __unicode__(self):
        return u'id: %s profile: %s %s %s' \
            % (self.id, self.name, self.first_surname, self.second_surname)

    def age_at(self, at_date):
        yo = ''
        if not self.dob is None:
            try:
                delta = datetime.combine(
                    at_date, time()) - datetime.combine(self.dob, time())
                yo = int(floor(delta.days / 365.25))
            except:
                yo = self.get_age()
        return yo

    def get_age(self):
        return self.age_at(date.today())

    def get_sex(self):
        if self.sex:
            return self.SEX[self.sex - 1][1]
        return ''

    def get_education(self):
        if self.education:
            return self.EDUCATION[self.education - 1][1]
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
            patient=self.user,
            date__lt=date.today()).order_by('-date')

        if appointments.count() > 0:
            lastAppointment = appointments[0]
        else:
            lastAppointment = ''

        return lastAppointment

    def get_next_real_appointment(self):
        appointments = Appointment.objects.filter(
            Q(patient=self.user, notify=True, status=settings.CONFIRMED),
            Q(date__gt=date.today()) |
            Q(date=date.today(),
              start_time__gte=datetime.time(datetime.now()))
        ).order_by('date')

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
                              settings.CANCELED_BY_DOCTOR]).order_by('date')

        for app in appointments:
            if not app.has_activity():
                nextAppointment = app
                break
        else:
            nextAppointment = ''

        return nextAppointment

    def get_conclusions(self):
        return Conclusion.objects.filter(
            appointment__patient=self.user).latest('date')

    def get_treatment(self, at_date=None):
        if at_date:
            return Medicine.objects.filter(Q(patient=self.user,
                                             created_at__lte=at_date,
                                             is_previous=False),
                                           Q(date__isnull=True) |
                                           Q(date__gte=at_date)).order_by('id')
        else:
            return Medicine.objects.filter(
                patient=self.user,
                date__isnull=True,
                is_previous=False).order_by('component')

    def get_pending_tasks(self):
        next_app = self.get_nextAppointment()
        tasks = []
        if next_app and datetime.combine(next_app.date, next_app.start_time) >= datetime.now():
            ddays = (next_app.date - date.today()).days
            tasks = Task.objects.filter(
                patient=self.user,
                self_administered=True,
                completed=False,
                assess=True,
                previous_days__gte=ddays,
                previous_days__gt=0).order_by('-creation_date')
        return tasks

    def get_assigned_tasks(self):
        tasks = Task.objects.filter(
            patient=self.user,
            self_administered=True,
            completed=False,
            assess=True,
            previous_days__gt=0).order_by('-creation_date')
        return tasks

    def get_anxiety_status(self, at_date=None, index=False, html=False):
        filter_option = Q(patient=self.user,
                          survey__code__in=(
                          settings.INITIAL_ASSESSMENT,
                          settings.ANXIETY_DEPRESSION_SURVEY
                          ),
                          completed=True,
                          assess=False)
        if at_date:
            filter_option = filter_option & Q(end_date__lte=at_date)
        try:
            for task in Task.objects.filter(filter_option).order_by('-end_date'):
                status = task.get_anxiety_status(index)
                if status != '':
                    break
            if html:
                if status[1] != 'success':
                    return '<span style="min-width:100px" class="label \
                        label-%s" >%s</span>' % (status[1], status[0])
                return ''
            else:
                return status
        except:
            return ''

    def get_depression_status(self, at_date=None, index=False, html=False):
        filter_option = Q(patient=self.user,
                          survey__code__in=(
                          settings.INITIAL_ASSESSMENT,
                          settings.ANXIETY_DEPRESSION_SURVEY
                          ),
                          completed=True,
                          assess=False)
        if at_date:
            filter_option = filter_option & Q(end_date__lte=at_date)
        try:
            for task in Task.objects.filter(filter_option).order_by('-end_date'):
                status = task.get_depression_status(index)
                if status != '':
                    break
            if html:
                if status[1] != 'success':
                    return '<span style="min-width:100px" class="label \
                        label-%s" >%s</span>' % (status[1], status[0])
                return ''
            else:
                return status
        except:
            return ''

    def get_unhope_status(self, at_date=None, index=False, html=False):
        filter_option = Q(patient=self.user,
                          survey__code=settings.UNHOPE_SURVEY,
                          completed=True,
                          assess=False)
        if at_date:
            filter_option = filter_option & Q(end_date__lte=at_date)
        try:
            for task in Task.objects.filter(filter_option).order_by('-end_date'):
                status = task.get_unhope_status(index)
                if status != '':
                    break
            if html:
                if status[1] != 'success':
                    return '<span style="min-width:100px" class="label \
                        label-%s" >%s</span>' % (status[1], status[0])
                return ''
            else:
                return status
        except:
            return ''

    def get_ybocs_status(self, at_date=None, index=False, html=False):
        filter_option = Q(patient=self.user,
                          survey__code=settings.YBOCS_SURVEY,
                          completed=True,
                          assess=False)
        if at_date:
            filter_option = filter_option & Q(end_date__lte=at_date)
        try:
            for task in Task.objects.filter(filter_option).order_by('-end_date'):
                status = task.get_ybocs_status(index)
                if status != '':
                    break
            if html:
                if status[1] != 'success':
                    return '<span style="min-width:100px" class="label \
                        label-%s" >%s</span>' % (status[1], status[0])
                return ''
            else:
                return status
        except:
            return ''

    def get_suicide_status(self, at_date=None, index=False, html=False):
        filter_option = Q(patient=self.user,
                          survey__code=settings.UNHOPE_SURVEY,
                          completed=True,
                          assess=False)
        if at_date:
            filter_option = filter_option & Q(end_date__lte=at_date)
        try:
            for task in Task.objects.filter(filter_option).order_by('-end_date'):
                status = task.get_suicide_status(index)
                if status != '':
                    break
            if html:
                if status[1] != 'success':
                    return '<span style="min-width:100px" class="label \
                        label-%s" >%s</span>' % (status[1], status[0])
                return ''
            else:
                return status
        except:
            return ''

    def get_medical_status(self, at_date=None, index=False, html=False):
        statuses = [self.get_anxiety_status(at_date, index, html),
                    self.get_depression_status(at_date, index, html),
                    self.get_unhope_status(at_date, index, html),
                    self.get_suicide_status(at_date, index, html),
                    self.get_ybocs_status(at_date, index, html)]
        return filter(None, statuses)

    def get_unread_messages(self):
        return Message.objects.get_pending_for_user(self.user)

    def get_mobile_phone(self):
        if self.phone1 and int(self.phone1) / int(10e7) in (6, 7):
            return self.phone1
        elif self.phone2 and int(self.phone2) / int(10e7) in (6, 7):
            return self.phone2
        else:
            return None

    def get_illness_set(self):
        illnesses = set()
        for i in self.illnesses.all().order_by('code'):
            parent = i
            while parent:
                illnesses.add(parent)
                parent = parent.parent
        return illnesses

    def is_banned(self):
        return self.user.banned_user.filter(Q(end_time__isnull=True) |
                                            Q(end_time__gte=datetime.now()))

    def get_scored_blocks(self, statistic=False):
        if self.is_doctor():
            if statistic:
                return Block.objects.filter(
                    is_scored=True).values('code', 'name').distinct()
            else:
                return Block.objects.filter(
                    locks_tasks__patient__profiles__doctor=self.user,
                    is_scored=True).values('code', 'name').distinct()
        else:
            return Block.objects.filter(
                blocks_tasks__patient=self.user,
                is_scored=True).values('code', 'name').distinct()

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"
        ordering = ['first_surname', 'second_surname', 'name', 'id']
