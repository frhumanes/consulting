# -*- encoding: utf-8 -*-
import re
from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.db import models

from managers import SlotManager, AppointmentManager
from log.models import TraceableModel
from datetime import date, datetime, time
from django.utils import formats

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
        on_delete=models.CASCADE)
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
    STATUS = (
        (0, _(u'Confirmada')),
        (1, _(u'Sin confimar')),
        (2, _(u'Cancelada por el médico')),
        (3, _(u'Anulada por el paciente')),
    )

    PAYMENT = (
          (_(u'Pagada'), 'success'),
          (_(u'Confirmada'), 'warning'),
          (_(u'Pendiente de pago'), 'error'),
          (_(u'Sin confirmar'), 'info'),
          (_(u'Cancelada'), ''),
          (_(u'No confirmada'), ''),
          (_(u'No asistió'), ''),
         )

    doctor = models.ForeignKey(User, related_name='appointment_doctor',limit_choices_to = {'profiles__role':settings.DOCTOR})

    patient = models.ForeignKey(User, related_name='appointment_patient',limit_choices_to = {'profiles__role':settings.PATIENT})

    app_type = models.ForeignKey(SlotType,
        related_name='appointment_slot_type', null=True, on_delete=models.SET_NULL)

    date = models.DateField(null=False, blank=False, help_text="Please use the following format: <em>DD/MM/YYYY</em>.")

    start_time = models.TimeField(null=False, blank=False, help_text="Please use the following format: <em>HH:mm</em>.")

    end_time = models.TimeField(null=False, blank=False, help_text="Please use the following format: <em>HH:mm</em>.")

    duration = models.IntegerField(null=False, blank=False, help_text="En minutos")
    description = models.TextField(max_length=5000, blank=True, null=True)

    objects = AppointmentManager()

    notify = models.BooleanField(_(u'Notificar cita'), default=True, help_text=_(u'Desmarcar para asignar citas virtuales que no requiren la presencia del paciente.'))

    status = models.IntegerField(_(u'Estado'), choices=STATUS, default=0)

    class Meta:
        get_latest_by = "start_time"
        verbose_name = "Cita"

    def __unicode__(self):
        return u'%s [%s-%s], %s' \
            % (self.date, self.start_time, self.end_time, self.patient)

    def is_first_appointment(self):
        return self == Appointment.objects.filter(patient=self.patient).order_by('date')[0]

    def is_editable(self):
        return not self.has_activity() and (datetime.now() - datetime.combine(self.date, self.end_time)).days <= settings.APP_EXPIRATION_DAYS

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
            if orig.is_confirmed() and self.is_canceled():
                status = 'deleted'
            elif orig.is_reserved() and self.is_confirmed():
                status = 'new'
            if orig.doctor != self.doctor:
                log = AppLog(appointment=self, pre_status=orig.status, comment=_(u'Cambio de médico'))
                log.save()
        else:
            status = 'new'

        self.description = re.sub('\*{2}.+\*{2}', '', self.description)
        if self.notify and not self.is_reserved() and status:
            if not self.warn_patient(status, orig):
                self.description += '\n' + _(u'**ATENCIÓN: Notificación no enviada. Se ruega contactar personalmente con el paciente**')

        super(Appointment, self).save(*args, **kw)

        if status:
            if not orig:
                log = AppLog(appointment=self, new_status=self.status)
            else:
                log = AppLog(appointment=self, pre_status=orig.status, new_status=self.status)
        log.save()


    def delete(self, *args, **kw):
        if self.notify and self.is_confirmed:
            self.warn_patient('deleted')
        super(Appointment, self).delete(*args, **kw)
            

    def warn_patient(self, action, app=None):
        subject = render_to_string('cal/app/notifications/'+action+'_email_subject.txt', {'user': self.patient.get_profile(),
                                          'app': self})
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        if self.patient.get_profile().email:
            try:
                message = render_to_string(
                    'cal/app/notifications/'+action+'_email_message.txt', 
                    {'user': self.patient.get_profile(),
                     'app': self, 
                     'orig':app, 
                     'LANGUAGE_CODE':'es'})
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, 
                        [self.patient.get_profile().email])
            except:
                return 0
        if settings.EMAIL2SMS:
            mobile = app.patient.get_profile().get_mobile_phone()
            if mobile:
                phone_mail = "%s%s%s" % (settings.PHONE_PREFIX,
                                         mobile,
                                         settings.SMS_GATEWAY)
                message = render_to_string(
                        'cal/app/notifications/'+action+'_sms_message.txt', 
                        {'user': self.patient.get_profile(),
                         'app': self, 
                         'orig':app, 
                         'LANGUAGE_CODE':'es'})
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [phone_mail])
        return 1

    def is_confirmed(self):
        return self.status == settings.CONFIRMED

    def is_canceled(self):
        return self.status == settings.CANCELED_BY_DOCTOR \
            or self.status == settings.CANCELED_BY_PATIENT

    def is_reserved(self):
        return self.status == settings.RESERVED

    def get_classes(self):
        classes = ""
        if self.is_reserved():
            classes += "muted "
        elif self.is_editable():
            classes += "text-info "
        else:
            if self.has_activity():
                classes += "text-success"
        return classes

    def get_payment_status(self, css=False):
        i = css and 1 or 0
        
        if Payment.objects.filter(appointment=self).count():
            return self.PAYMENT[0][i]
        else:
            if self.has_activity(): #DONE
                return self.PAYMENT[2][i]
            elif self.is_canceled(): #CANCELED
                return self.PAYMENT[4][i]
            elif self.is_editable(): #SCHEDULED
                if self.is_confirmed():
                    return self.PAYMENT[1][i]
                elif self.is_editable():
                    return self.PAYMENT[3][i]
            elif not self.is_editable(): #OUTDATED
                if self.is_confirmed():
                    return self.PAYMENT[6][i]
                else:
                    return self.PAYMENT[5][i]

        return ''

    def get_payment_class(self):
        return self.get_payment_status(True)


    def get_styles(self):
        styles = ""
        if self.is_canceled():
            styles += "text-decoration: line-through; "
        return styles

    def get_log(self):
        return list(self.applog_appointment.all().order_by('-date'))



class AppLog(models.Model):
    STATUS = (
        (0, _(u'Confirmada')),
        (1, _(u'Sin corfimar')),
        (2, _(u'Cancelada por el médico')),
        (3, _(u'Anulada por el paciente')),
    )
    appointment = models.ForeignKey(Appointment, 
                                    related_name='applog_appointment')
    date = models.DateTimeField(auto_now_add=True)
    pre_status = models.IntegerField(choices=STATUS, null=True)
    new_status = models.IntegerField(choices=STATUS, null=True)
    comment = models.TextField(max_length=5000, blank=True, null=True)

    def __unicode__(self):
        change = "Fecha/hora cambiada"
        if self.pre_status is None:
            change = _(u'Cita creada')
        elif self.new_status is None:
            change = self.comment
        elif self.pre_status != self.new_status:
            change = _(u'Estado cambiado: ') + AppLog.STATUS[self.pre_status][1] + ' >> ' + AppLog.STATUS[self.new_status][1]
        return u'%s %s' % (formats.date_format(self.date, "SHORT_DATETIME_FORMAT"), change)

class Payment(TraceableModel):
    METHODS = (
        (1, _(u'Efectivo')),
        (2, _(u'Tarjeta')),
        (3, _(u'Aseguradora')),
        (4, _(u'Otros')),
        )
    appointment = models.OneToOneField(Appointment, primary_key=True, 
                                    related_name='payment_appointment')
    method = models.IntegerField(_(u'Forma de pago'), choices=METHODS)
    date = models.DateField(_(u'Fecha de pago'), default=date.today)
    value = models.DecimalField(_(u'Importe'), max_digits=5, decimal_places=2, null=True, blank=True)
    discount = models.IntegerField(_(u'Descuento / bonificación'), default=0)

    def __unicode__(self):
        if self.value:
            return u'%s %s (%d€)' % (formats.date_format(self.date, "SHORT_DATE_FORMAT"), self.appointment.get_payment_status(), self.value)
        else:
            return u'%s %s' % (formats.date_format(self.date, "SHORT_DATE_FORMAT"), self.appointment.get_payment_status())

    class Meta:
        verbose_name = "Registro de pago"