# -*- encoding: utf-8 -*-

from django.db import models
from django.db.models import Max
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings

from log.models import TraceableModel
from survey.models import Survey, Block, Question, Option
from medicament.models import Component
from illness.models import Illness
from cal.models import Appointment


class Task(TraceableModel):
    patient = models.ForeignKey(User, related_name='patient_tasks')

    survey = models.ForeignKey(Survey, related_name="survey_tasks")

    questions = models.ManyToManyField(Question,
                                        related_name="questions_tasks",
                                        blank=True, null=True)

    treated_blocks = models.ManyToManyField(Block, related_name='blocks_tasks')

    appointment = models.ForeignKey(Appointment,
                                    related_name="appointment_tasks")

    self_administered = models.NullBooleanField(_(u'¿Tarea autoadministrada?'))

    creation_date = models.DateTimeField(_(u'Fecha de creación de la tarea'),
                                        auto_now_add=True)

    start_date = models.DateTimeField(_(u'Fecha de comienzo de la encuesta'),
                                        blank=True, null=True)

    end_date = models.DateTimeField(_(u'Fecha de finalización de la encuesta'),
                                    blank=True, null=True)

    from_date = models.DateField(
                    _(u'Fecha a partir de la cual puede realizar la encuesta'),
                    blank=True, null=True)

    to_date = models.DateField(
                    _(u'Fecha hasta la que puede realizar la encuesta'),
                    blank=True, null=True)

    assess = models.BooleanField(_(u'¿Seguir valorando la encuesta?'),
                                default=True)

    completed = models.BooleanField(
                    _(u'¿Ha contestado todas las preguntas de la encuesta?'),
                    default=False)

    observations = models.CharField(max_length=5000, blank=True,
                                            null=True)

    def __unicode__(self):
        return u'id: %s task: %s %s %s' \
            % (self.id, self.patient, self.survey, self.creation_date)

    def get_self_administered(self):
        if self.self_administered:
            return _(u'Sí')
        else:
            return _(u'No')

    def if_from_date(self):
        if self.from_date != None:
            return self.from_date
        else:
            return ''

    def if_to_date(self):
        if self.to_date != None:
            return self.to_date
        else:
            return ''

    def get_answers(self):
        answers = []
        for r in self.task_results.values('block').annotate(Max('date'),Max('id')).order_by():
            answers += Result.objects.get(id=r['id__max']).options.all()
        return answers

    def is_completed(self):
        if self.treated_blocks.count() == self.survey.num_blocks:
            return self.completed
        else:
            return False

    def get_time_interval(self):
        return self.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(code__startswith='DS')

    def get_af_dict(self):
        dic = {}
        for opt in self.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(question__code__startswith='AF').exclude(text='Ninguno'):
            if opt.text in dic:
                dic[opt.text].append(opt.question.get_af_illness())
            else:
                dic[opt.text] = [opt.question.get_af_illness()]
        return dic

    def get_ap_list(self):
        return self.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(question__code__startswith='AP')

    def get_organicity_list(self):
        return self.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(question__code__in=['AN','AE','AT','AI','AO'])

    def get_rp_list(self):
        return self.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(code__startswith='RP')

    def get_comorbidity_list(self):
        return self.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(code__in=['AP7','AP8','AP9','AP10','AP11','AP12'])

    def calculate_mark_by_code(self, code):
        answers = self.get_answers()
        mark = 0
        for a in answers:
            if a.code.startswith(code):
                mark += a.weight
        return mark

    def calculate_beck_mark(self):
        answers = self.get_answers()
        mark = 0
        for a in answers:
            if a.code.startswith('B'):
                mark += a.weight #* 5 / q.question_options.aggregate(Max('weight'))['weight__max']
        return mark

    def calculate_hamilton_mark(self):
        answers = self.get_answers()
        mark = 0
        submarks = {}
        kind = self.treated_blocks.all().aggregate(Max('kind'))['kind__max']
        for a in answers:
            if not a.code.startswith('H') or a.code.startswith('Hd'):
                continue
            item = a.code.split('.')[0]
            if kind == settings.EXTENSO:
                if item in submarks:
                    submarks[item] += a.weight
                else:
                    submarks[item] = a.weight
            else:
                submarks[item] = a.weight
                mark += a.weight
        if kind == settings.EXTENSO:
            for code, value in submarks.items():
                submarks[code] = float(value)/Question.objects.filter(code__startswith=code+'.').count()
                mark += submarks[code]
        return mark, submarks

    def get_ave_status(self):
        l = settings.AVE.keys()
        l.sort()
        ave_mark = self.calculate_mark_by_code('AVE')
        for value in l:
            if ave_mark < value:
                return settings.AVE[value]

    def get_depression_status(self):
        l = settings.BECK.keys()
        l.sort()
        beck_mark = self.calculate_beck_mark()
        for value in l:
            if beck_mark < value:
                return settings.BECK[value]

    def get_anxiety_status(self):
        l = settings.HAMILTON.keys()
        l.sort()
        hamilton_mark, hamilton_submarks = self.calculate_hamilton_mark()
        for value in l:
            if hamilton_mark < value:
                return settings.HAMILTON[value]




class Medicine(TraceableModel):
    BEFORE_AFTER_CHOICES = (
        (settings.BEFORE, _(u'Anterior')),
        (settings.AFTER, _(u'Posterior')),
    )
    patient = models.ForeignKey(User, related_name='patient_medicines')

    component = models.ForeignKey(Component,
                                related_name='component_medicines',
                                blank=True, null=True)
    conclusion = models.ForeignKey('Conclusion',
                                related_name='conclusion_medicines',
                                blank=True, null=True)
    result = models.ForeignKey('Result', related_name='result_medicines',
                              blank=True, null=True)

    before_after_first_appointment = models.IntegerField(
                                        _(u'Anterior/Posterior\
                                        Primera Cita'),
                                        choices=BEFORE_AFTER_CHOICES,
                                        blank=True, null=True)
    before_after_symptom = models.IntegerField(_(u'Anterior/Posterior\
                                    síntomas psiquiátricos'),
                                    choices=BEFORE_AFTER_CHOICES,
                                    blank=True, null=True)
    months = models.IntegerField(_(u'Número de meses de toma del fármaco'),
                                    blank=True, null=True)
    posology = models.CharField(_(u'Posología (mg/día)'), max_length=255,
                                    blank=True)
    date = models.DateTimeField(_(u'Fecha'), auto_now_add=True)



    def __unicode__(self):
        return u'id: %s medicine: %s' % (self.id, self.component)

    def get_before_after_symptom(self):
        if self.before_after_symptom == settings.BEFORE:
            before_after_symptom = _(u'Anterior')
        else:
            before_after_symptom = _(u'Posterior')

        return before_after_symptom

    def get_before_after_first_appointment(self):
        if self.before_after_first_appointment == settings.BEFORE:
            before_after_first_appointment = _(u'Anterior')
        else:
            before_after_first_appointment = _(u'Posterior')

        return before_after_first_appointment


class Result(TraceableModel):
    patient = models.ForeignKey(User, related_name='patient_results')

    survey = models.ForeignKey(Survey, related_name="survey_results")

    options = models.ManyToManyField(Option, related_name="options_results")

    task = models.ForeignKey(Task, related_name="task_results")

    block = models.ForeignKey(Block, related_name="block_results")

    appointment = models.ForeignKey(Appointment,
                                    related_name="appointment_results",
                                    blank=True, null=True)

    date = models.DateTimeField(_(u'Fecha'), auto_now_add=True)

    symptoms_worsening = models.CharField(max_length=5000, blank=True,
                                            null=True)

    def __unicode__(self):
        return u'id: %s result: %s %s %s' % (self.id, self.patient, self.survey, self.block)


class Conclusion(TraceableModel):
    patient = models.ForeignKey(User, related_name='patient_conclusions')

    result = models.ForeignKey(Result, unique=True,
                                related_name='result_conclusion',
                                blank=True, null=True)

    appointment = models.ForeignKey(Appointment,
                                    related_name="appointment_conclusions")

    observation = models.CharField(max_length=5000, blank=True, null=True)

    recommendation = models.CharField(max_length=5000, blank=True, null=True)

    task = models.ForeignKey(Task, related_name="task_conclusions", blank=True, null=True)

    date = models.DateTimeField(_(u'Fecha'), auto_now_add=True)

    def __unicode__(self):
        return u'id: %s conclusion: %s %s' \
                                % (self.id, self.patient, self.appointment)


class Report(TraceableModel):
    patient = models.ForeignKey(User, related_name='patient_reports')

    illness = models.ForeignKey(Illness, related_name='illness_reports')

    survey = models.ForeignKey(Survey, related_name="survey_reports")

    result = models.ForeignKey(Result, related_name='result_reports')

    date = models.DateTimeField(_(u'Fecha del Informe'), auto_now_add=True)

    def __unicode__(self):
        return u'id: %s report: %s %s' % (self.id, self.patient, self.illness)