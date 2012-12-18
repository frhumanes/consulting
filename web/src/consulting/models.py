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
from formula.models import Formula, Dimension, Variable
from numbers import Real

from django.core.cache import cache


class Task(TraceableModel):
    KIND = (
        (settings.GENERAL, _(u'General')),
        (settings.EXTENSO, _(u'Extenso')),
        (settings.ABREVIADO, _(u'Abreviado')),
    )

    patient = models.ForeignKey(User, related_name='patient_tasks',limit_choices_to = {'profiles__role':settings.PATIENT})

    survey = models.ForeignKey(Survey, related_name="survey_tasks")

    kind = models.IntegerField(_(u'Tipo'), choices=KIND, default=settings.GENERAL)

    questions = models.ManyToManyField(Question,
                                        related_name="questions_tasks",
                                        blank=True, null=True, 
                                        help_text=u"Si no se selecciona ninguna se mostrarán las predeterminadas de la encuesta.")

    treated_blocks = models.ManyToManyField(Block, related_name='blocks_tasks')

    appointment = models.ForeignKey(Appointment,
                                    related_name="appointment_tasks", null=True)

    self_administered = models.NullBooleanField(_(u'Tarea autoadministrada'))

    creation_date = models.DateTimeField(_(u'Fecha de creación de la tarea'),
                                        auto_now_add=True)

    start_date = models.DateTimeField(_(u'Fecha de comienzo de la encuesta'),
                                        blank=True, null=True)

    end_date = models.DateTimeField(_(u'Fecha de finalización de la encuesta'),
                                    blank=True, null=True)

    previous_days = models.IntegerField(
                    _(u'Disponibilidad para el paciente'),
                    default=settings.DAYS_BEFORE_SURVEY, help_text=u"días antes de la próxima cita")


    assess = models.BooleanField(_(u'Seguir valorando la encuesta'),
                                default=True)

    completed = models.BooleanField(
                    _(u'Tarea completada'),
                    default=False)

    observations = models.TextField(max_length=5000, blank=True,
                                            null=True)

    def __unicode__(self):
        return u'id: %s task: %s %s %s' \
            % (self.id, self.patient, self.survey, self.creation_date)

    def get_self_administered(self):
        if self.self_administered:
            return _(u'Sí')
        else:
            return _(u'No')

    def get_answers_by_block(self):
        answers = {}
        for r in self.task_results.values('block').annotate(Max('date'),Max('id')).order_by():
            block = []
            for qid, qtext in Answer.objects.filter(result__id=r['id__max']).values_list('question__id','question__text').distinct().order_by('question__id'):
                block.append({'question':qtext,
                              'answers': [str(a) for a in Answer.objects.filter(result__id=r['id__max'],question__id=qid)]})
            answers[r['block']] = block
        return answers

    def get_answers(self):
        #Cache
        _answers = cache.get('answers_'+str(self.id))
        if _answers:
            return _answers
        answers = []
        for r in self.task_results.values('block').annotate(Max('date'),Max('id')).order_by():
            answers += Answer.objects.filter(result__id=r['id__max']).select_related().all().order_by("question__id")
        cache.set('answers_'+str(self.id), list(answers)) 
        return answers

    def is_completed(self):
        if self.treated_blocks.count() == self.survey.num_blocks:
            return self.completed
        else:
            return False

    def get_time_interval(self):
        answer = Answer.objects.filter(result__block=settings.PRECEDENT_RISK_FACTOR, option__code__startswith='DS', result__task=self).latest('result__id')
        return "%s %s" % (answer.value, answer.option.text)

    def get_af_dict(self):
        dic = {}
        result = Answer.objects.filter(result__task=self, result__block__code=settings.PRECEDENT_RISK_FACTOR).aggregate(latest=Max('result__id'))
        answer = Answer.objects.filter(result__id=result['latest'], option__code__startswith='AF').exclude(option__text='Ninguno')
        for a in answer:
            opt = a.option
            if opt and opt.text in dic:
                dic[opt.text].append(opt.question.get_af_illness())
            else:
                dic[opt.text] = [opt.question.get_af_illness()]
        return dic

    def get_ap_list(self):
        result = Answer.objects.filter(result__task=self, result__block__code=settings.PRECEDENT_RISK_FACTOR).aggregate(latest=Max('result__id'))
        answer = Answer.objects.filter(result__id=result['latest'], option__question__code='AP').exclude(option__text='Ninguno').order_by('-id')
        return answer

    def get_organicity_list(self):
        result = Answer.objects.filter(result__task=self, result__block__code=settings.PRECEDENT_RISK_FACTOR).aggregate(latest=Max('result__id'))
        answer = Answer.objects.filter(result__id=result['latest'], option__question__code__in=['AN','AE','AT','AI','AO']).exclude(option__text='Ninguno').order_by('-id')
        return answer

    def get_rp_list(self):
        return self.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(code__startswith='RP')

    def get_comorbidity_list(self):
        return self.task_results.filter(block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(code__in=['AP7','AP8','AP9','AP10','AP11','AP12'])

    def get_ave_list(self):
        answers = self.get_answers()
        l = []
        for answer in answers:
            a = answer.option
            if a and a.code.startswith('AVE'):
                l.append(a.id)
        return l

    def calculate_mark_by_code(self, code):
        answers = self.get_answers()
        mark = 0
        for answer in answers:
            a = answer.option
            if a and a.code.startswith(code):
                mark += a.weight
        return mark

    def calculate_beck_mark(self):
        answers = self.get_answers()
        beck_answers = filter(lambda a: a.question.code.startswith('B'), answers)
        if len(beck_answers) != Question.objects.filter(code__startswith='B').count():
            return None
        mark = 0
        for answer in beck_answers:
            a = answer.option
            mark += a.weight #* 5 / q.question_options.aggregate(Max('weight'))['weight__max']
        return mark

    def calculate_hamilton_mark(self):
        answers = self.get_answers()
        mark = None
        submarks = {}
        kind = self.kind
        ham_answers = filter(lambda a: a.question.code.startswith('H'), answers)
        categories = self.survey.blocks.get(kind=kind).categories.filter()
        ham_questions = 0
        for category in categories:
            ham_questions += category.questions.filter(kind__in=[settings.UNISEX, self.patient.get_profile().sex], code__startswith='H').count()
        if ham_questions != len(ham_answers):
            return mark, submarks
        mark = 0
        for answer in ham_answers:
            a = answer.option
            if a and (not a.code.startswith('H') or a.code.startswith('Hd')):
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

    def get_depression_status(self, index=False):
        _status = cache.get('status_'+str(self.id), {})
        if _status and 'depression' in _status:
            if index:
                return _status['depression'][0]
            else:
                return _status['depression'][1]
        l = settings.BECK.keys()
        l.sort()
        beck_mark = self.calculate_beck_mark()
        if beck_mark is None:
            return ''
        for value in l:
            if beck_mark < value:
                _status['depression'] = [l.index(value), settings.BECK[value]]
                cache.set('status_'+str(self.id), _status)
                if index:
                    return l.index(value)
                else:
                    return settings.BECK[value]

    def get_anxiety_status(self, index=False):
        _status = cache.get('status_'+str(self.id), {})
        if _status and 'anxiety' in _status:
            if index:
                return _status['anxiety'][0]
            else:
                return _status['anxiety'][1]
        l = settings.HAMILTON.keys()
        l.sort()
        hamilton_mark, hamilton_submarks = self.calculate_hamilton_mark()
        if hamilton_mark is None:
            return ''
        for value in l:
            if hamilton_mark < value:
                _status['anxiety'] = (l.index(value), settings.HAMILTON[value])
                cache.set('status_'+str(self.id), _status)
                if index:
                    return l.index(value)
                else:
                    return settings.HAMILTON[value]

    def get_kind(self):
        if self.kind == settings.GENERAL:
            return 'General'
        elif self.kind == settings.EXTENSO:
            return 'Extenso'
        else:
            return 'Abreviado'

    def get_list_variables(self, num=None, exclude=[]):
        marks = self.get_variables_mark()
        lv = []
        if num != None:
            values = marks.values()
            values.sort()
            if num <= len(values):
                n_mark = values[-num]
            else:
                n_mark = 0
        else:
            n_mark = 0
        for var, mark in marks.items():
            if mark >= n_mark and not var.code in exclude:
                lv.append((var.id, var.name))
        return lv

    def get_variables_mark(self):
        _marks = cache.get('marks_'+str(self.id))
        if _marks:
            return _marks
        answers = self.get_answers()
        marks = {}
        variable_tuple = None
        
        kind = self.kind

        #for f in Formula.objects.filter(kind=kind):
        for f in Formula.objects.filter(kind__in=(settings.GENERAL, self.kind),
           variable__variables_categories__categories_blocks__in=self.treated_blocks.all()).distinct():
            total = None
            for item in f.polynomial.split('+'):
                for answer in answers:
                    a = answer
                    if a.question.code == item:
                        if not total:
                            total = 0
                        try:
                            total += a.option.weight
                        except:
                            pass
                        break
            if total != None:
                if f.variable in marks:
                    marks[f.variable]+=(float(total) * float(f.factor))
                else:
                    marks[f.variable]=(float(total) * float(f.factor))
            else:
                marks[f.variable] = ''
        #sorted(marks.items(), key=lambda x: -x[1])
        cache.set('marks_'+str(self.id), marks)
        return marks

    def get_dimensions_mark(self, variables_mark=None):
        marks = {}
        if variables_mark is None:
            variables_mark = self.get_variables_mark()
        for d in Dimension.objects.all():
            total = 0
            for item in d.polynomial.split('+'):
                variable = Variable.objects.get(code=item)
                if variable in variables_mark and isinstance(variables_mark[variable], Real) and variables_mark[variable] >= 0:
                        total += variables_mark[variable]
                else:
                    return {}
            if d.name in marks:
                marks[d.name] += (float(total) * float(d.factor))
            else:
                marks[d.name] = (float(total) * float(d.factor))
        return marks

    def is_scored(self):
        return self.survey.code in [settings.ANXIETY_DEPRESSION_SURVEY, settings.ADHERENCE_TREATMENT, settings.PREVIOUS_STUDY, settings.INITIAL_ASSESSMENT]

    class Meta:
        verbose_name = "Tarea"
        ordering = ("end_date", "created_at")



class Medicine(TraceableModel):
    patient = models.ForeignKey(User, related_name='patient_medicines',limit_choices_to = {'profiles__role':settings.PATIENT})

    component = models.ForeignKey(Component,
                                related_name='component_medicines',
                                blank=True, null=True)
    appointment = models.ForeignKey(Appointment, 
                                    related_name='appointment_medicines',
                                    blank=True, null=True)

    is_previous = models.BooleanField(_(u'Tratamiento previo'),
                                        default=False)
    after_symptoms = models.BooleanField(_(u'Posterior a\
                                    los síntomas'), default=True)
    months = models.DecimalField(_(u'Número de meses de toma del fármaco'),
                                    max_digits=5, decimal_places=2,
                                    blank=True, null=True)
    posology = models.IntegerField(_(u'Posología (mg/día)'))
    dosification = models.CharField(_(u'Modo de administración'), 
                                    max_length=255, blank=True, 
                                    null=True, default='')
    date = models.DateTimeField(_(u'Fecha Fin'), null=True)



    def __unicode__(self):
        return u'id: %s medicine: %s' % (self.id, self.component)

    def get_before_after_symptom(self):
        if not self.after_symptoms:
            before_after_symptom = _(u'Anterior')
        else:
            before_after_symptom = _(u'Posterior')

        return before_after_symptom

    def get_before_after_first_appointment(self):
        if self.is_previous:
            before_after_first_appointment = _(u'Anterior')
        else:
            before_after_first_appointment = _(u'Posterior')

        return before_after_first_appointment

    def is_active(self):
        return self.date is None

    class Meta:
        verbose_name = "Tratamiento"


class Result(TraceableModel):
    patient = models.ForeignKey(User, related_name='patient_results',limit_choices_to = {'profiles__role':settings.PATIENT})

    survey = models.ForeignKey(Survey, related_name="survey_results")

    options = models.ManyToManyField(Option, related_name="options_results", through='Answer')

    task = models.ForeignKey(Task, related_name="task_results")

    block = models.ForeignKey(Block, related_name="block_results")

    appointment = models.ForeignKey(Appointment,
                                    related_name="appointment_results",
                                    blank=True, null=True)

    date = models.DateTimeField(_(u'Fecha'), auto_now_add=True)


    def __unicode__(self):
        return u'id: %s result: %s %s %s' % (self.id, self.patient, self.survey, self.block)

    class Meta:
        verbose_name = "Resultado"


class Conclusion(TraceableModel):
    appointment = models.ForeignKey(Appointment,
                                    related_name="appointment_conclusions")

    observation = models.TextField(max_length=5000, blank=True, null=True)

    recommendation = models.TextField(max_length=5000, blank=True, null=True)

    date = models.DateTimeField(_(u'Fecha'), auto_now_add=True)

    def __unicode__(self):
        return u'id: %s conclusion: %s %s' \
                                % (self.id, self.appointment.patient, self.appointment)

    class Meta:
        verbose_name = u"Conclusión"
        verbose_name_plural = "Conclusiones"


class Answer(models.Model):
    result = models.ForeignKey(Result, related_name='result_answers')
    option = models.ForeignKey(Option, related_name='option_answers', null=True)
    question = models.ForeignKey(Question, related_name='question_answers')
    value = models.CharField(max_length=50, blank=True, null=True)

    def __unicode__(self):
        try:
            if (not self.option or self.option.text.startswith('Otr')) and self.value:
                return self.value
            elif self.value and self.option.question.code in ['DS']:
                return u'%s %s' % (self.value, self.option.text)
            else:
                return u'%s' % (self.option.text)
        except:
            return str(self.id)

    class Meta:
        verbose_name = "Respuesta"

class DummyReport(models.Model):
    # Required to avoid Django try to access to non-exist 'reports' table when deleting either Profile or Task objects 
    task = models.IntegerField(null=True)
    patient = models.IntegerField(null=True)
    date = models.DateTimeField(_(u'Fecha del Informe'), null=True)
    sex = models.IntegerField(null=True)
    profession = models.CharField(max_length=150)
    age = models.IntegerField(null=True)
    treatment = models.IntegerField(null=True)
    variables = models.IntegerField(null=True)
    aves = models.IntegerField(null=True)
    dimensions = models.IntegerField(null=True)
    status = models.IntegerField(null=True)

    class Meta:
        db_table = 'reports'
