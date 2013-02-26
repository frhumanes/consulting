# -*- encoding: utf-8 -*-
from consulting.models import Task
from stadistic.models import Report


def generate_reports(full=False):
    i = 0
    if full:
        Report.objects.all().delete()
    for task in Task.objects.filter(completed=True):
        try:
            report = Report.objects.get(task=task)
            if report.date == task.end_date:
                continue
        except:
            report = Report()
        report.task = task
        report.blocks = [block.code for block in task.treated_blocks.all()]
        report.date = report.task.end_date
        report.created_by = task.created_by
        report.patient = task.patient.get_profile()
        age = report.patient.age_at(report.date)
        report.age = age and age or None
        report.sex = report.patient.sex
        report.education = report.patient.education
        report.marital = report.patient.status
        report.illnesses = [ill.code for ill in task.patient.get_profile().illnesses.all()]
        report.treatment = [m.component.name for m in report.patient.get_treatment(report.date)]
        report.profession = task.patient.get_profile().profession
        report.variables = dict((k.name, v) for (k, v) in task.get_variables_mark().items())
        report.dimensions = dict((k.name, v) for (k, v) in task.get_dimensions_mark().items())
        report.status={u'Depresión': report.patient.get_depression_status(task.end_date, True),
                       u'Ansiedad': report.patient.get_anxiety_status(task.end_date, True),
                       u'Suicidio': report.patient.get_suicide_status(task.end_date, True),
                       u'Desesperanza': report.patient.get_unhope_status(task.end_date, True),
                       u'Obsesión/Compulsión': report.patient.get_ybocs_status(task.end_date, True)
                      }
        report.aves = task.get_ave_list()
        report.save()
        i += 1
    return i