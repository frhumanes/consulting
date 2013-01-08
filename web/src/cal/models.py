# -*- encoding: utf-8 -*-
import re
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.db import models

from managers import SlotManager, AppointmentManager
from log.models import TraceableModel
from datetime import date, datetime, time

from django.template.loader import render_to_string
from django.conf import settings
from django.core.mail import send_mail


class Vacation(TraceableModel):
    doctor = models.ForeignKey(User, related_name='vacation_doctor',limit_choices_to = {'profiles__role':settings.DOCTOR})
    date = models.DateField(null=False, blank=False, help_text="Please use the following format: <em>DD/MM/YYYY</em>.")
    description = models.TextField(max_length=5000, blank=True, null=True)

    class Meta:
        unique_together = ('doctor', 'date')
        verbose_name = _(u'Ausencia')

    def __unicode__(self):
        return u'%s, %s' % (self.date, self.doctor)


class Event(TraceableModel):
    doctor = models.ForeignKey(User, 
                    related_name='event_doctor', 
                    limit_choices_to = {'profiles__role':settings.DOCTOR})
    date = models.DateField(null=False, blank=False, help_text="Please use the following format: <em>DD/MM/YYYY</em>.")
    start_time = models.TimeField(null=False, blank=False, help_text="Please use the following format: <em>HH:mm</em>.")
    end_time = models.TimeField(null=False, blank=False, help_text="Please use the following format: <em>HH:mm</em>.")
    description = models.TextField(max_length=5000, blank=True, null=True)

    class Meta:
        unique_together = ('doctor', 'date', 'start_time', 'end_time')
        verbose_name = "Evento"

    def __unicode__(self):
       return u'%s [%s-%s], %s' % (self.date, 
                                  self.start_time, self.end_time,
                                  self.doctor)

    def get_duration(self):
        return (datetime.combine(date.today(), self.end_time) - datetime.combine(date.today(), self.start_time)).seconds / 60

class SlotType(TraceableModel):
    doctor = models.ForeignKey(User, related_name='entry_type_doctor',limit_choices_to = {'profiles__role':settings.DOCTOR})
    title = models.CharField(max_length=255)
    duration = models.IntegerField(null=False, blank=False, help_text="En minutos")
    description = models.TextField(max_length=5000, blank=True, null=True)

    class Meta:
        verbose_name = "Tipo de cita"
        verbose_name_plural = "Tipos de cita"

    def __unicode__(self):
        return u"%s [%d]" % (self.title, self.duration)


class Slot(TraceableModel):
    WEEKDAYS = (
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    )

    MONTH = (
        (0, _('January')),
        (1, _('February')),
        (2, _('March')),
        (3, _('April')),
        (4, _('May')),
        (5, _('June')),
        (6, _('July')),
        (7, _('August')),
        (8, _('September')),
        (9, _('October')),
        (10, _('November')),
        (11, _('December')),
    )

    creator = models.ForeignKey(User, related_name='slot_creator')
    slot_type = models.ForeignKey(SlotType, related_name='slot_event_type',
        on_delete=models.PROTECT)
    weekday = models.IntegerField(choices=WEEKDAYS)
    month = models.IntegerField(choices=MONTH)
    year = models.IntegerField()
    start_time = models.TimeField(null=False, blank=False, help_text="Please use the following format: <em>HH:mm</em>.")
    end_time = models.TimeField(null=False, blank=False, help_text="Please use the following format: <em>HH:mm</em>.")
    description = models.TextField(max_length=5000, blank=True, null=True)

    #reserved = models.BooleanField(default=False)

    # manager
    objects = SlotManager()

    def __unicode__(self):
        return u'%s [%s-%s], %s' \
            % (self.slot_type.title, self.start_time, self.end_time, self.creator)

    class Meta:
        ordering = ["month", "weekday", "start_time"]
        verbose_name = "Preferencia"


class Appointment(TraceableModel):

    doctor = models.ForeignKey(User, related_name='appointment_doctor',limit_choices_to = {'profiles__role':settings.DOCTOR})

    patient = models.ForeignKey(User, related_name='appointment_patient',limit_choices_to = {'profiles__role':settings.PATIENT})

    app_type = models.ForeignKey(SlotType,
        related_name='appointment_slot_type', null=True)

    date = models.DateField(null=False, blank=False, help_text="Please use the following format: <em>DD/MM/YYYY</em>.")

    start_time = models.TimeField(null=False, blank=False, help_text="Please use the following format: <em>HH:mm</em>.")

    end_time = models.TimeField(null=False, blank=False, help_text="Please use the following format: <em>HH:mm</em>.")

    duration = models.IntegerField(null=False, blank=False, help_text="En minutos")
    description = models.TextField(max_length=5000, blank=True, null=True)

    objects = AppointmentManager()

    notify = models.BooleanField(_(u'Notificar cita'), default=True, help_text=_(u'Desmarcar para asignar citas virtuales que no requiren la presencia del paciente.'))

    class Meta:
        get_latest_by = "start_time"
        verbose_name = "Cita"

    def __unicode__(self):
        return u'%s [%s-%s], %s' \
            % (self.date, self.start_time, self.end_time, self.patient)

    def is_first_appointment(self):
        return self == Appointment.objects.filter(patient=self.patient).order_by('date')[0]

    def is_editable(self):
        return datetime.combine(self.date, self.end_time) >= datetime.now()

    def has_activity(self):
        return bool(self.appointment_tasks.all().count() or self.appointment_conclusions.all().count())

    def is_over(self):
         return bool(self.appointment_conclusions.all().count())

    def save(self, *args, **kw):
        status = None
        orig = None
        self.duration = (datetime.combine(date.today(), self.end_time) - datetime.combine(date.today(), self.start_time)).seconds/60
        if self.pk is not None:
            orig = Appointment.objects.get(pk=self.pk)
            if orig.date != self.date or orig.start_time != self.start_time or orig.end_time != self.end_time:
                status = 'changed'
        else:
            status = 'new'

        self.description = re.sub('\*{2}.+\*{2}', '', self.description)
        if self.notify and status:
            if not self.warn_patient(status, orig):
                self.description += '\n' + _(u'**ATENCIÓN: Notificación no enviada. Se ruega contactar personalmente con el paciente**')

        super(Appointment, self).save(*args, **kw)


    def delete(self, *args, **kw):
        if self.notify:
            self.warn_patient('deleted')
        super(Appointment, self).delete(*args, **kw)
            

    def warn_patient(self, action, app=None):
        if self.patient.get_profile().email:
            try:
                subject = render_to_string('cal/app/notifications/'+action+'_email_subject.txt', {'user': self.patient.get_profile(),
                                          'app': self})
                # Email subject *must not* contain newlines
                subject = ''.join(subject.splitlines())

                message = render_to_string('cal/app/notifications/'+action+'_email_message.txt', {'user': self.patient.get_profile(),
                                        'app': self, 'orig':app, 'LANGUAGE_CODE':'es'})

                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, 
                            [self.patient.get_profile().email])
            except:
                return 0
        return 1