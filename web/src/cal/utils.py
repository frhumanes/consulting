# -*- encoding: utf-8 -*-

from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from datetime import date, datetime, timedelta
import calendar
import time

from cal.models import Appointment
from cal.models import Vacation
from cal.models import Event
from cal.models import Slot


mnames = (
    _("January"), _("February"), _("March"), _("April"), _("May"), _("June"),
    _("July"), _("August"), _("September"), _("October"), _("November"),
    _("December"),)


def create_calendar(year, month, doctor=None):
    cal = calendar.Calendar()
    month_days = cal.itermonthdays(int(year), int(month))
    nyear, nmonth, nday = time.localtime()[:3]
    lst = [[]]
    week = 0

    for day in month_days:
        if len(lst[week]) == 7:
            lst.append([])
            week += 1
        apps = Appointment.objects.none()
        current = False
        vacations = False
        events = False
        if day:
            if doctor:
                apps = Appointment.objects.filter(
                    date__year=year, date__month=month,
                    date__day=day, doctor=doctor)
            else:
                apps = Appointment.objects.filter(date__year=year,
                            date__month=month, date__day=day)

            if day == nday and year == nyear and month == nmonth:
                current = True

            vacations = check_vacations(doctor, year, month, day)
            events = check_events(doctor, year, month, day)

        lst[week].append((day, apps, current, vacations, events))
    return lst


def check_vacations(doctor, year, month, day):
    vacations = Vacation.objects.filter(doctor=doctor, date__year=year,
        date__month=month, date__day=day)
    return vacations


def check_events(doctor, year, month, day):
    events = Event.objects.filter(doctor=doctor, date__year=year,
        date__month=month, date__day=day)
    return events


def check_vacations_or_events(doctor, year, month, day):
    vacations_or_events = False

    vacations = Vacation.objects.filter(doctor=doctor, date__year=year,
        date__month=month, date__day=day)

    if vacations.count() == 0:
        events = Event.objects.filter(doctor=doctor, date__year=year,
            date__month=month, date__day=day)
        if not events.count() == 0:
            vacations_or_events = True
    else:
        vacations_or_events = True

    return vacations_or_events


def add_minutes(tm, minutes):
    fulldate = datetime(1, 1, 1, tm[3], tm[4], tm[5])
    fulldate = fulldate + timedelta(minutes=minutes)
    return fulldate.time()


def get_weekday(date):
    wday = date.timetuple()[6]
    return wday


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


def reminders(request):
    year, month, day = time.localtime()[:3]
    reminders = Appointment.objects.filter(date__year=year, date__month=month,
        date__day=day, doctor=request.user, remind=True)
    tomorrow = datetime.now() + timedelta(days=1)
    year, month, day = tomorrow.timetuple()[:3]
    return list(reminders) + list(Appointment.objects.filter(date__year=year,
        date__month=month, date__day=day, doctor=request.user, remind=True))
