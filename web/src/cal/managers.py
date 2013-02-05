# -*- encoding: utf-8 -*-

from datetime import datetime, date
from django.db.models import Manager
from cal import settings as app_settings


class SlotManager(Manager):
    def get_entries_for_user(self, user):
        return self.get_query_set().filter(doctor=user).order_by('-weekday')


class AppointmentManager(Manager):
    def availability(self, doctor, app_date, app_to_check=None, edit=False):
        #from django.db.models import Q
        #Q(app_type__vacation=True) | Q(app_type__event=True),

        apps = self.get_query_set()\
                    .filter(
                        doctor=doctor,
                        date__year=app_date.year,
                        date__month=app_date.month,
                        date__day=app_date.day)\
                    .order_by('start_time')

        if edit and not app_to_check is None:
            apps = apps.exclude(id=app_to_check.id).order_by('start_time')

        from cal.models import Event, Vacation
        vacation = Vacation.objects\
            .filter(
                doctor=doctor,
                date__year=app_date.year,
                date__month=app_date.month,
                date__day=app_date.day)
        if vacation.count():
            return (False, None)
        events = Event.objects\
            .filter(
                doctor=doctor,
                date__year=app_date.year,
                date__month=app_date.month,
                date__day=app_date.day)\
            .order_by('start_time')

        app_and_evt = list(apps) + list(events)

        if app_and_evt:
            app_and_evt = sorted(app_and_evt, key=lambda x: x.start_time)

        free_intervals = None
        matchings = None
        available = True
        matched = True

        if len(app_and_evt) > 0:
            free_intervals = []

            if app_and_evt[0].start_time > app_settings.START_TIME:
                z = datetime.combine(date.today(),
                    app_and_evt[0].start_time) - \
                    datetime.combine(date.today(), app_settings.START_TIME)
                #if z.seconds > 0:
                first = {
                        'id': app_and_evt[0].id,
                        'start_time': app_settings.START_TIME,
                        'end_time': app_and_evt[0].start_time,
                        'duration': z.seconds / 60}
                free_intervals.append(first)
                # a = app_settings.START_TIME
                # a = apps[0].start_time
                a = app_and_evt[0].end_time
            else:
                a = app_and_evt[0].end_time

            appointments = app_and_evt[1:len(app_and_evt)]

            for app in appointments:
                z = datetime.combine(date.today(), app.start_time) - \
                    datetime.combine(date.today(), a)
                #if z.seconds > 0:
                interval = {
                            'id': app.id,
                            'start_time': a,
                            'end_time': app.start_time,
                            'duration': z.seconds / 60}
                a = app.end_time
                free_intervals.append(interval)

            latest = app_and_evt[len(app_and_evt) - 1]

            if latest.end_time < app_settings.END_TIME:
                z = datetime.combine(date.today(), app_settings.END_TIME) - \
                        datetime.combine(date.today(), latest.end_time)
                #if z.seconds > 0:
                latest_ = {
                            'id': latest.id,
                            'start_time': latest.end_time,
                            'end_time': app_settings.END_TIME,
                            'duration': z.seconds / 60}

                free_intervals.append(latest_)

            available = True if len(free_intervals) > 0 else False #WTF!!

        if not app_to_check is None and not free_intervals is None:
            matchings = []

            for interval in free_intervals:
                if app_to_check.start_time >= interval['start_time']\
                    and app_to_check.start_time <= interval['end_time']\
                    and app_to_check.end_time <= interval['end_time']\
                    and app_to_check.end_time >= interval['start_time']:
                    matchings.append(interval)

            matched = len(matchings) > 0

        if free_intervals is None and matchings is None:
            available = True
            matchings = True

        return (available and matched, free_intervals)
