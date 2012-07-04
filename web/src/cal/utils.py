# -*- encoding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from datetime import date, datetime, timedelta
import calendar
import time

from cal.models import Appointment
from cal.models import Slot


mnames = (
    _("January"), _("February"), _("March"), _("April"), _("May"), _("June"),
    _("July"), _("August"), _("September"), _("October"), _("November"),
    _("December"),)


def create_calendar(year, month, user=None):
    # init variables
    cal = calendar.Calendar()
    month_days = cal.itermonthdays(int(year), int(month))
    nyear, nmonth, nday = time.localtime()[:3]
    lst = [[]]
    week = 0

    # make month lists containing list of days for each week
    # each day tuple will contain list of slots and 'current' indicator
    for day in month_days:
        apps = current = False   # are there slots for this day; current day?
        if day:
            if user:
                apps = Appointment.objects.filter(date__year=year,
                    date__month=month, date__day=day, doctor=user)
            else:
                apps = Appointment.objects.filter(date__year=year,
                    date__month=month, date__day=day)
            if day == nday and year == nyear and month == nmonth:
                current = True

        lst[week].append((day, apps, current))
        if len(lst[week]) == 7:
            lst.append([])
            week += 1
    return lst


def add_minutes(tm, minutes):
    fulldate = datetime(1, 1, 1, tm[3], tm[4], tm[5])
    fulldate = fulldate + timedelta(minutes=minutes)
    return fulldate.time()


def get_weekday(date):
    wday = date.timetuple()[6]
    return wday


def reminders(request):
    """Return the list of reminders for today and tomorrow."""
    year, month, day = time.localtime()[:3]
    reminders = Appointment.objects.filter(date__year=year, date__month=month,
        date__day=day, doctor=request.user, remind=True)
    tomorrow = datetime.now() + timedelta(days=1)
    year, month, day = tomorrow.timetuple()[:3]
    return list(reminders) + list(Appointment.objects.filter(date__year=year,
        date__month=month, date__day=day, doctor=request.user, remind=True))


def get_doctor_preferences(year=None, month=None, day=None, doctor=None):
    if not doctor is None:
        doctor = get_object_or_404(User, pk=int(doctor))

        if not day is None:
            selected_date = date(int(year), int(month), int(day))
            weekday = get_weekday(selected_date)

            slots = Slot.objects \
            .filter(creator=doctor, date__year=year, date__month=month,
                weekday=weekday)
        else:
            slots = Slot.objects \
            .filter(creator=doctor, date__year=year, date__month=month)

        return slots
    else:
        return Slot.objects.none()
