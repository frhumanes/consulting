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
        profile = task.patient.get_profile()
        report.task = task.id
        report.blocks = [block.code for block in task.treated_blocks.all()]
        report.date = task.end_date
        report.created_by = task.created_by
        report.patient = profile.id
        age = profile.age_at(report.date)
        report.age = age and age or None
        report.sex = profile.sex
        report.education = profile.education
        report.marital = profile.status
        report.illnesses = [ill.code for ill in profile.illnesses.all()]
        report.treatment = [m.component.name for m in profile.get_treatment(report.date)]
        report.profession = profile.profession
        report.variables = dict((k.name, v) for (k, v) in task.get_variables_mark().items())
        report.dimensions = dict((k.name, v) for (k, v) in task.get_dimensions_mark().items())
        report.status={u'Depresión': profile.get_depression_status(task.end_date, True),
                       u'Ansiedad': profile.get_anxiety_status(task.end_date, True),
                       u'Suicidio': profile.get_suicide_status(task.end_date, True),
                       u'Desesperanza': profile.get_unhope_status(task.end_date, True),
                       u'Obsesión/Compulsión': profile.get_ybocs_status(task.end_date, True)
                      }
        report.aves = task.get_ave_list()
        report.save()
        i += 1
    return i