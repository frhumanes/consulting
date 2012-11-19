# -*- encoding: utf-8 -*-
from django.conf import settings
from consulting.models import Task
from stadistic.models import Report

def generate_reports(full=False):
    if full:
        Report.objects.all().delete()
    for task in Task.objects.filter(completed=True):
        try:
            report = Report.objects.get(task=task)
            if report.end_date == task.end_date:
                continue
        except:
            report = Report()
        report.task = task
        report.date = report.task.end_date
        report.created_by = task.created_by
        report.patient = task.patient.get_profile()
        report.age = report.patient.get_age()
        report.sex = report.patient.sex
        report.treatment = dict((m.component.name, int(m.posology)) for m in report.patient.get_treatment(report.date))
        report.profession = task.patient.get_profile().profession
        report.variables = dict((k.name, v) for (k, v) in task.get_variables_mark().items())
        try:
            adherence_task = Task.objects.filter(appointment=task.appointment, survey__code=settings.ADHERENCE_TREATMENT).latest('end_date')
            report.variables[u'Adherencia'] = int(adherence_task.get_answers()[0].option.weight)
        except:
            pass
        report.dimensions = task.get_dimensions_mark()
        report.status={u'Depresión': report.patient.get_depression_status(task.end_date, True),
                       u'Ansiedad': report.patient.get_anxiety_status(task.end_date, True)
                      }
        report.aves = task.get_ave_list()
        report.save()