# -*- encoding: utf-8 -*-
from django.db import models
from django.db.models import Max
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.models import User
from django.conf import settings

from log.models import TraceableModel
from survey.models import Survey, Block, Question, Option
from medicament.models import Component
from cal.models import Appointment
from formula.models import Formula, Dimension, Variable, Scale, Risk
from numbers import Real

from django.core.cache import cache
import re
pattern = re.compile('[a-zA-Z]+\w*')


class Task(TraceableModel):
    KIND = (
        (settings.GENERAL, _(u'General')),
        (settings.EXTENSO, _(u'Extenso')),
        (settings.ABREVIADO, _(u'Abreviado')),
    )

    patient = models.ForeignKey(
        User,
        related_name='patient_tasks',
        limit_choices_to={'profiles__role': settings.PATIENT})

    survey = models.ForeignKey(Survey, related_name="survey_tasks")

    kind = models.IntegerField(_(u'Tipo'), choices=KIND,
                               default=settings.GENERAL)

    questions = models.ManyToManyField(
        Question,
        related_name="questions_tasks",
        blank=True,
        null=True,
        help_text=_(u"Si no se selecciona ninguna se mostrarán las \
            predeterminadas de la encuesta."))

    treated_blocks = models.ManyToManyField(Block, related_name='blocks_tasks')

    appointment = models.ForeignKey(Appointment,
                                    related_name="appointment_tasks",
                                    null=True)

    self_administered = models.NullBooleanField(_(u'Tarea autoadministrada'))

    creation_date = models.DateTimeField(_(u'Fecha de creación de la tarea'),
                                         auto_now_add=True)

    start_date = models.DateTimeField(_(u'Fecha de comienzo de la encuesta'),
                                      blank=True, null=True)

    end_date = models.DateTimeField(_(u'Fecha de finalización de la encuesta'),
                                    blank=True, null=True)

    from_date = models.DateTimeField(_(u'Fecha de apertura de la encuesta'),
                                      blank=True, null=True)

    to_date = models.DateTimeField(_(u'Fecha de cierre de la encuesta'),
                                    blank=True, null=True)

    previous_days = models.IntegerField(
        _(u'Disponibilidad para el paciente'),
        default=settings.DAYS_BEFORE_SURVEY,
        help_text=u"días antes de la próxima cita")

    assess = models.BooleanField(_(u'Seguir valorando la encuesta'),
                                 default=True)

    completed = models.BooleanField(_(u'Tarea completada'), default=False)

    observations = models.TextField(blank=True, null=True)

    def __unicode__(self):
        return u'%s %s %s' \
            % (self.patient, self.survey, self.creation_date)

    def get_self_administered(self):
        if self.self_administered:
            return _(u'Sí')
        else:
            return _(u'No')

    def get_answers_by_block(self):
        answers = {}
        for r in self.task_results.values('block').annotate(Max('date'),Max('id')).order_by('block__code'):
            block = []
            for qid, qtext in Answer.objects.filter(result__id=r['id__max']).values_list('question__id','question__text').distinct().order_by('question__id'):
                block.append({
                    'question': qtext,
                    'answers': [
                        str(a) for a in Answer.objects.filter(
                            result__id=r['id__max'], question__id=qid)]})
            answers[r['block']] = block
        return sorted(answers.iteritems(), key=lambda block: -block[0])

    def get_answers(self):
        #Cache
        _answers = cache.get('answers_' + str(self.id))
        if _answers and self.completed:
            return _answers
        answers = []
        for r in self.task_results.values('block').annotate(Max('date'),Max('id')).order_by():
            answers += Answer.objects.filter(
                result__id=r['id__max']).select_related().all().order_by(
                    "question__id")
        cache.set('answers_' + str(self.id), list(answers))
        return answers

    def is_completed(self):
        if self.treated_blocks.count() == self.survey.num_blocks(self.kind):
            return self.completed
        else:
            return False

    def get_time_interval(self):
        answer = Answer.objects.filter(
            result__block=settings.PRECEDENT_RISK_FACTOR,
            option__code__startswith='DS',
            result__task=self).latest('result__id')
        return "%s %s" % (answer.value, answer.option.text)

    def get_af_dict(self):
        dic = {}
        result = Answer.objects.filter(
            result__task=self,
            result__block__code=settings.PRECEDENT_RISK_FACTOR).aggregate(
                latest=Max('result__id'))
        answer = Answer.objects.filter(
            result__id=result['latest'],
            option__code__startswith='AF').exclude(option__text='Ninguno')
        for a in answer:
            opt = a.option
            if opt and opt.text in dic:
                dic[opt.text].append(opt.question.get_af_illness())
            else:
                dic[opt.text] = [opt.question.get_af_illness()]
        return dic

    def get_ap_list(self):
        result = Answer.objects.filter(
            result__task=self,
            result__block__code=settings.PRECEDENT_RISK_FACTOR).aggregate(
                latest=Max('result__id'))
        answer = Answer.objects.filter(
            result__id=result['latest'],
            option__question__code='AP').exclude(
                option__text='Ninguno').order_by('-id')
        return answer

    def get_organicity_list(self):
        result = Answer.objects.filter(
            result__task=self,
            result__block__code=settings.PRECEDENT_RISK_FACTOR).aggregate(
                latest=Max('result__id'))
        answer = Answer.objects.filter(
            result__id=result['latest'],
            option__question__code__in=['AN', 'AE', 'AT', 'AI', 'AO']).exclude(
                option__text='Ninguno').order_by('-id')
        return answer

    def get_rp_list(self):
        return self.task_results.filter(
            block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(
                code__startswith='RP')

    def get_comorbidity_list(self):
        return self.task_results.filter(
            block=settings.PRECEDENT_RISK_FACTOR).latest('id').options.filter(
                code__in=['AP7', 'AP8', 'AP9', 'AP10', 'AP11', 'AP12'])

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

    def calculate_unhope_mark(self, preresult=None):
        if not self.survey or self.survey.code != settings.UNHOPE_SURVEY:
            return None
        return self.calculate_mark_by_code('U')


    def calculate_beck_mark(self, preresult=None):
        if not self.survey or not self.survey.code in [settings.ANXIETY_DEPRESSION_SURVEY, settings.INITIAL_ASSESSMENT]:
            return None
        answers = self.get_answers()
        beck_answers = filter(
            lambda a: a.question.code.startswith('B'), answers)
        if len(beck_answers) != Question.objects.filter(code__startswith='B').count():
            return None
        mark = 0
        for answer in beck_answers:
            a = answer.option
            mark += a.weight
        return mark

    def calculate_hamilton_mark(self, preresult=None):
        if not self.survey or not self.survey.code in [settings.ANXIETY_DEPRESSION_SURVEY, settings.INITIAL_ASSESSMENT]:
            return None, {}
        answers = self.get_answers()
        mark = None
        submarks = {}
        kind = self.kind
        ham_answers = filter(
            lambda a: a.question.code.startswith('H'), answers)
        categories = self.survey.blocks.get(kind=kind).categories.filter()
        ham_questions = 0
        for category in categories:
            ham_questions += category.questions.filter(
                kind__in=[settings.UNISEX, self.patient.get_profile().sex],
                code__startswith='H').count()
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
                submarks[code] = float(value) / Question.objects.filter(
                    code__startswith=code + '.').count()
                mark += submarks[code]
        return mark, submarks

    def calculate_euroqol_mark(self, preresult=None):
        if not self.survey or not self.survey.code == settings.EUROQOL_5D:
            return None
        answers = self.get_answers()
        mark = None
        submarks = self.get_variables_mark()
        kind = self.kind
        eq_answers = filter(
            lambda a: a.question.code.startswith('EQ'), answers)
        categories = self.survey.blocks.get(kind=kind).categories.filter()
        eq_questions = 0
        for category in categories:
            eq_questions += category.questions.filter(
                kind__in=[settings.UNISEX, self.patient.get_profile().sex],
                code__startswith='EQ').count()
        if eq_questions != len(eq_answers):
            return mark, submarks
        constant, N3 = 0, 0
        for a in eq_answers:
            if a.question.code == 'EQ6':
                continue
            if a.option.weight > 0:
                constant = 0.1502
            if a.option.weight == 2:
                N3 = 0.2119
        mark = 1 - constant - N3 - sum(submarks.values()[:5])
        return mark, submarks

    def calculate_asthma_mark(self, preresult=None):
        if not self.survey or not self.survey.code == settings.ASTHMA:
            return None
        answers = self.get_answers()
        highest = 0
        for a in answers:
            highest = max(highest, a.option.weight)
        return highest

    def calculate_asthma_cronos_mark(self, preresult=None):
        answers = self.get_answers()
        submarks, fev_mark, exa_mark = [], 0, 0
        result = 0
        
        for answer in answers:
            a = answer.option
            if a:
                if a.code.startswith('ASMA') and a.code <= 'ASMA4':
                    submarks.append(a.weight)
                elif a.code == 'ASMA5': #FEV or PEF
                    fev_mark = a.weight
                elif a.code == 'ASMA6': #Exacerbations
                    exa_mark = a.weight


        # First step
        items = sum(i > 1 for i in submarks)

        if 0 < items < 3:
            result = 1 #Partialy controled
        elif items > 2:
            result = 2 #Bad controled
            return result #2 is the highest value

        #Second step
        if fev_mark > 1:
            result = 1
        if exa_mark > 1:
            result = 1
        elif exa_mark > 2:
            result = 2 #Bad controled
            return result #2 is the highest value

        #Third step (result is 0 or 1)
        acq_mark = self.calculate_scale(Scale.objects.get(key='acq'))
        if acq_mark >= 1.5:
            result = 1

        act_mark = self.calculate_scale(Scale.objects.get(key='act'))
        if 15 < act_mark < 20:
            result = 1
        elif act_mark <= 15:
            result = 2

        return result


    def fix_comorbility_mark(self, preresult=None):
        age = self.patient.get_profile().age_at(self.end_date)
        result = preresult
        if age and age > 50:
            result += (age - 50) / 10 + 1
        return result


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
        if not num is None:
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
        _marks = cache.get('marks_' + str(self.id))
        if _marks:
            return _marks
        answers = self.get_answers()
        marks = {}

        for f in Formula.objects.filter(kind__in=(settings.GENERAL, self.kind),
           variable__variables_categories__categories_blocks__in=self.treated_blocks.all()).distinct():

            polynomial = f.polynomial
            total = polynomial.isdigit() and int(polynomial) or None
            for item in reversed(sorted(pattern.findall(polynomial), key=len)):
                value = 0
                for answer in answers:
                    a = answer
                    if a.question.code == item:
                        if not total:
                            total = 0
                        try:
                            value += a.option.weight
                        except:
                            print f
                        #break
                polynomial = polynomial.replace(item, str(value))
                if not total is None:
                    total += value

            try:
                total = eval(polynomial)
            except:
                print "P(x):%s; %s" % (f.polynomial, polynomial)
                
            if not total is None:
                if f.variable in marks:
                    marks[f.variable] += (float(total) * float(f.factor))
                else:
                    marks[f.variable] = (float(total) * float(f.factor))
            else:
                marks[f.variable] = ''
        #sorted(marks.items(), key=lambda x: -x[1])
        cache.set('marks_' + str(self.id), marks)
        return marks

    def get_dimensions_mark(self, variables_mark=None):
        marks = {}
        if variables_mark is None:
            variables_mark = self.get_variables_mark()
        for d in Dimension.objects.filter(dimension_variables__variables_categories__categories_blocks__in=self.treated_blocks.all()).distinct():
            total = 0
            polynomial = d.polynomial
            for item in reversed(sorted(pattern.findall(polynomial), key=len)):
                if not item:
                    continue
                variables = Variable.objects.filter(code=item)
                found = False
                for variable in variables:
                    if variable in variables_mark and isinstance(variables_mark[variable], Real):
                            value = variables_mark[variable]
                            found = True
                            polynomial = polynomial.replace(item, str(value))
                if not found:
                    return {}
            try:
                total = eval(polynomial)
            except:
                print "P(x):%s; %s" % (d.polynomial, polynomial)
            if d in marks:
                marks[d] += (float(total) * float(d.factor))
            else:
                marks[d] = (float(total) * float(d.factor))
        return marks

    def calculate_scale(self, scale):
        _scale = cache.get('task_' + str(self.id) + '_' + scale.key)
        if _scale:
            return _scale
        result = 0
        if scale.polynomial:
            if scale.polynomial == settings.EXTENSO:
                code_questions = scale.polynomial.split('+')
                answers = self.get_answers()
                for answer in answers:
                    if answer.question.code in code_questions:
                        result += answer.option.weight
            else:
                result = self.calculate_mark_by_code(scale.polynomial.replace('*',''))
            result = result * scale.factor
        else:
            result = None

        if scale.action:
            try:
                result = getattr(self, scale.action)(result)
            except:
                return None
            if isinstance(result, (list, tuple)):
                result = result[0]


        cache.set('task_' + str(self.id) + '_' + scale.key, result)
        
        return result

    def get_scales(self, exclude=None):
        scales = []
        if not self.survey:
            return None
        for scale in self.survey.scales.all():
            score = self.calculate_scale(scale)
            if not score is exclude:
                scales.append({'name': scale.name,
                               'mark': score,
                               'status': scale.get_level(score),
                               'hash': scale.key,
                               'scale': scale})
            
        return scales

    def get_level(self, scale):
        return scale.get_level(self.calculate_scale(scale))


    def is_scored(self):
        for block in self.treated_blocks:
            if block.is_scored:
                return True
        return False

    def get_average_marks(self):
        _avg = cache.get('avg_' + str(self.survey.code))
        if _avg:
            return _avg
        avg_data = {}

        if self.survey.code == settings.EPQR_SURVEY:
            for key, value in settings.EPQR_A.items():
                avg_data[Variable.objects.get(code=key)] = value
        else:
            for t in Task.objects.filter(survey=self.survey, completed=True):
                for var, mark in t.get_variables_mark().items():
                    if mark >= 0 and mark != '':
                        p = t.patient.get_profile()
                        if (var in avg_data.keys() and
                                p.sex in avg_data[var].keys()):
                            avg_data[var][p.sex].append(mark)
                        elif var in avg_data.keys():
                            avg_data[var][p.sex] = [mark, ]
                        else:
                            avg_data[var] = {p.sex: [mark, ]}
            for var, marks in avg_data.items():
                for key, l in marks.items():
                    if l:
                        avg_data[var][key] = reduce(lambda x, y: x + y, l) / len(l)
                    else:
                        avg_data[var][key] = 0
        cache.set('avg_' + str(self.survey.code), avg_data)
        return avg_data

    def clear_cache(self):
        from django.core.cache import get_cache
        cache = get_cache('default')
        cache.clear()

    def check_risks(self):
        variables = self.get_variables_mark()
        risks = []
        for v, mark in variables.iteritems():
            cond = v.get_active_condition(mark)
            if cond:
                risks.append(cond.risk)

        try:
            from collections import Counter
            risks = sorted(Counter(risks).items(), key=lambda x: -x[0].criticity)
            for r, n in risks:
                if n >= r.coincidences:
                    return r
        except:
            pass

    class Meta:
        verbose_name = "Tarea"
        ordering = ("end_date", "created_at")



class Medicine(TraceableModel):
    patient = models.ForeignKey(
        User,
        related_name='patient_medicines',
        limit_choices_to={'profiles__role': settings.PATIENT})

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

    posology = models.DecimalField(_(u'Posología (mg/día)'),
                                   max_digits=9, decimal_places=4)

    dosification = models.CharField(_(u'Modo de administración'),
                                    max_length=255, blank=True,
                                    null=True, default='')

    date = models.DateTimeField(_(u'Fecha Fin'), null=True)

    def __unicode__(self):
        return u'%s' % (self.component)

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
    patient = models.ForeignKey(
        User,
        related_name='patient_results',
        limit_choices_to={'profiles__role': settings.PATIENT})

    survey = models.ForeignKey(Survey, related_name="survey_results")

    options = models.ManyToManyField(Option,
                                     related_name="options_results",
                                     through='Answer')

    task = models.ForeignKey(Task, related_name="task_results")

    block = models.ForeignKey(Block, related_name="block_results")

    appointment = models.ForeignKey(Appointment,
                                    related_name="appointment_results",
                                    blank=True, null=True)

    date = models.DateTimeField(_(u'Fecha'), auto_now_add=True)

    def __unicode__(self):
        return u'%s %s %s' % (self.patient, self.survey, self.block)

    class Meta:
        verbose_name = "Resultado"


class Conclusion(TraceableModel):
    appointment = models.ForeignKey(Appointment, unique=False,
                                    related_name="appointment_conclusions")

    observation = models.TextField(blank=True, null=True)

    recommendation = models.TextField(blank=True, null=True)

    extra = models.FileField(blank=True, null=True, upload_to="documents/%Y/%m/%d")

    date = models.DateTimeField(_(u'Fecha'), auto_now_add=True)

    def __unicode__(self):
        return u'%s %s' % (self.appointment.patient, self.appointment)

    class Meta:
        verbose_name = u"Conclusión"
        verbose_name_plural = "Conclusiones"


class Answer(models.Model):
    result = models.ForeignKey(Result, related_name='result_answers')
    option = models.ForeignKey(Option,
                               related_name='option_answers',
                               null=True)
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

class Alert(models.Model):
    task = models.ForeignKey(Task)
    risk = models.ForeignKey(Risk)
    creation_date = models.DateTimeField(_(u'Fecha de creación de la alerta'),
                                         auto_now_add=True)
    revised_date = models.DateTimeField(_(u'Fecha de revisión'), null=True)

    class Meta:
        ordering = ['-creation_date']

    def __unicode__(self):
        return u"%s - %s" % (self.task, self.risk.name)


class DummyReport(models.Model):
    # Required to avoid Django try to access to non-exist 'reports' table
    # when deleting either Profile or Task objects
    task_id = models.IntegerField(null=True)
    patient_id = models.IntegerField(null=True)
    date = models.DateTimeField(_(u'Fecha del Informe'), null=True)
    blocks = models.IntegerField(null=True)
    illnesses = models.IntegerField(null=True)
    sex = models.IntegerField(null=True)
    education = models.IntegerField(null=True)
    marital = models.IntegerField(null=True)
    profession = models.CharField(max_length=150)
    age = models.IntegerField(null=True)
    treatment = models.IntegerField(null=True)
    variables = models.IntegerField(null=True)
    aves = models.IntegerField(null=True)
    dimensions = models.IntegerField(null=True)
    status = models.IntegerField(null=True)

    class Meta:
        db_table = 'reports'
