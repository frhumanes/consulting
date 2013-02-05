# -*- encoding: utf-8 -*-
import calendar
import time
import copy

from django.utils.translation import ugettext_lazy as _
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from django.conf import settings
from datetime import date, datetime, timedelta
from datetime import time as dtime
from cal.models import Appointment
from cal.models import Vacation
from cal.models import Event
from cal.models import Slot
import cal.settings as cal_settings
from userprofile.models import Profile


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
        available = cal_settings.TOTAL_HOURS.seconds / 60
        if len(lst[week]) == 7:
            lst.append([])
            week += 1
        apps = Appointment.objects.none()
        current = False
        vacations = []
        events = []
        if day:
            if doctor:
                apps = Appointment.objects.filter(
                    date__year=year, date__month=month,
                    date__day=day, doctor=doctor,
                    status__in=[settings.CONFIRMED, settings.RESERVED]
                    ).order_by('start_time')
            else:
                apps = Appointment.objects.filter(date__year=year,
                            date__month=month, date__day=day
                            ).order_by('start_time')

            if day == nday and year == nyear and month == nmonth:
                current = True

            vacations = check_vacations(doctor, year, month, day)
            events = check_events(doctor, year, month, day)
            if vacations:
                available = 0
            else:
                for e in events:
                    available -= e.get_duration()
                for a in apps:
                    available -= a.duration
            available = max(0, available)

        lst[week].append([day, list(apps), current, list(vacations), list(events), available])
    return lst


def check_vacations(doctor, year, month, day):
    vacations = Vacation.objects.filter(doctor=doctor, date__year=year,
        date__month=month, date__day=day)
    return vacations


def check_events(doctor, year, month, day):
    events = list(Event.objects.filter(doctor=doctor, date__year=year,
        date__month=month, date__day=day))
    for p in Profile.objects.filter(dob__month=month, dob__day=day, doctor=doctor):
        e = Event()
        e.doctor = p.doctor
        e.start_time = dtime(0, 0)
        e.end_time = dtime(0, 0)
        e.description = _(u'Cumpleaños de') + ' ' + p.get_full_name()
        events.insert(0, e)
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

def check_scheduled_apps(app, number, period, interval):
    ok, fails = [], []
    orig_day = app.date.day
    for n in range(int(number)):
        if int(interval) == 7:
            d = datetime.combine(app.date, app.start_time) + timedelta(days=7*int(period))
            app.date = d.date()
        elif int(interval) == 30:
            month = app.date.month - 1 + int(period)
            year = app.date.year + month / 12
            month = month % 12 + 1
            try:
                app.date = date(year, month, orig_day)
            except ValueError:
                if month == 2:
                    app.date = date(year, month, 28)
                if app.date.day == 31:
                    app.date = date(year, month, 30)

        elif int(interval) == 365:
            app.date = date(app.date.year + int(period), app.date.month, app.date.day)

        if not Appointment.objects.availability(app.doctor, app.date, app)[0]:
            fails.append(copy.deepcopy(app))
        else:
            ok.append(copy.deepcopy(app))
    return ok, fails



def add_minutes(tm, minutes):
    if isinstance(tm, dtime):
        fulldate = datetime.combine(date.today(), tm)
    else:
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
            .filter(creator=doctor, year=year, month=int(month)-1,
                weekday=weekday)
        else:
            slots = Slot.objects \
            .filter(creator=doctor, year=year, month=int(month)-1)
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
