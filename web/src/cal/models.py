# -*- encoding: utf-8 -*-

from django.db import models
from django.contrib.auth.models import User

from managers import SlotManager, AppointmentManager
from log.models import TraceableModel


class SlotType(TraceableModel):
    doctor = models.ForeignKey(User, related_name='entry_type_doctor')
    title = models.CharField(max_length=256)
    duration = models.IntegerField()

    def __unicode__(self):
        return self.title


class Slot(TraceableModel):
    WEEKDAYS = (
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    )

    creator = models.ForeignKey(User, related_name='slot_creator')
    slot_type = models.ForeignKey(SlotType, related_name='slot_event_type')
    weekday = models.IntegerField(choices=WEEKDAYS)
    date = models.DateField(null=False, blank=False)
    start_time = models.TimeField(null=False, blank=False)
    end_time = models.TimeField(null=False, blank=False)
    duration = models.IntegerField(null=False, blank=False)
    note = models.CharField(max_length=5000, blank=True, null=True)
    remind = models.BooleanField(default=False)

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
        related_name='appointment_slot_type')

    date = models.DateField(null=False, blank=False)
    start_time = models.TimeField(null=False, blank=False)
    end_time = models.TimeField(null=False, blank=False)
    duration = models.IntegerField(null=False, blank=False)
    note = models.CharField(max_length=5000, blank=True, null=True)
    remind = models.BooleanField(default=False)

    objects = AppointmentManager()

    class Meta:
        get_latest_by = "start_time"

    def __unicode__(self):
        return u'id: %s %s slot at %s' \
            % (self.id, self.app_type, self.start_time)
