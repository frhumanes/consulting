# -*- encoding: utf-8 -*-

from django.utils.translation import ugettext as _
from django.contrib.auth.models import User
from django.db import models

from managers import SlotManager, AppointmentManager
from log.models import TraceableModel


class Vacation(TraceableModel):
    doctor = models.ForeignKey(User, related_name='vacation_doctor')
    date = models.DateField(null=False, blank=False)
    description = models.CharField(max_length=5000, blank=True, null=True)

    class Meta:
        unique_together = ('doctor', 'date')

    def __unicode__(self):
        return u'id: %s %s slot at %s' \
            % (self.id, self.doctor, self.date)


class Event(TraceableModel):
    doctor = models.ForeignKey(User, related_name='event_doctor')
    date = models.DateField(null=False, blank=False)
    start_time = models.TimeField(null=False, blank=False)
    end_time = models.TimeField(null=False, blank=False)
    description = models.CharField(max_length=5000, blank=True, null=True)

    class Meta:
        unique_together = ('doctor', 'date', 'start_time', 'end_time')

    def __unicode__(self):
        return u'id: %s %s slot at %s' \
            % (self.id, self.doctor, self.date)


class SlotType(TraceableModel):
    doctor = models.ForeignKey(User, related_name='entry_type_doctor')
    title = models.CharField(max_length=256)
    duration = models.IntegerField()
    description = models.CharField(max_length=5000, blank=True, null=True)

    def __unicode__(self):
        return self.title


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

    creator = models.ForeignKey(User, related_name='slot_creator')
    slot_type = models.ForeignKey(SlotType, related_name='slot_event_type',
        on_delete=models.PROTECT)
    weekday = models.IntegerField(choices=WEEKDAYS)
    date = models.DateField(null=False, blank=False)
    start_time = models.TimeField(null=False, blank=False)
    end_time = models.TimeField(null=False, blank=False)
    duration = models.IntegerField(null=False, blank=False)
    description = models.CharField(max_length=5000, blank=True, null=True)

    #reserved = models.BooleanField(default=False)

    # manager
    objects = SlotManager()

    def __unicode__(self):
        return u'id: %s %s slot at %s' \
            % (self.id, self.slot_type, self.start_time)

    class Meta:
        ordering = ["weekday", "start_time"]


class Appointment(TraceableModel):
    doctor = models.ForeignKey(User, related_name='appointment_doctor')
    patient = models.ForeignKey(User, related_name='appointment_patient')
    app_type = models.ForeignKey(SlotType,
        related_name='appointment_slot_type', null=True)

    date = models.DateField(null=False, blank=False)
    start_time = models.TimeField(null=False, blank=False)
    end_time = models.TimeField(null=False, blank=False)
    duration = models.IntegerField(null=False, blank=False)
    description = models.CharField(max_length=5000, blank=True, null=True)

    objects = AppointmentManager()

    class Meta:
        get_latest_by = "start_time"

    def __unicode__(self):
        return u'id: %s %s slot at %s' \
            % (self.id, self.app_type, self.start_time)