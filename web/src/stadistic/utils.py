# -*- encoding: utf-8 -*-
from consulting.models import Task
from stadistic.models import Report

def generate_reports(full=False):
    if full:
        Report.objects.all().delete()
    for task in Task.objects.filter(completed=True):
        try:
            report = Report.objects.get(task=task)
        except:
            report = Report()
        report.task = task
        report.date = report.task.end_date
        report.created_by = task.created_by
        report.patient = task.patient.get_profile()
        report.age = report.patient.get_age()
        report.sex = report.patient.sex
        report.profession = task.patient.get_profile().profession
        report.variables = { k.name: v for k, v in task.get_variables_mark().items()}
        report.dimensions = task.get_dimensions_mark()
        report.status={u'Depresión': report.patient.get_depression_status(task.end_date, True),
                       u'Ansiedad': report.patient.get_anxiety_status(task.end_date, True)
                      }
        report.aves = task.get_ave_list()
        report.save()