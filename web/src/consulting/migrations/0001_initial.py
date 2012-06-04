# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Report'
        db.create_table('consulting_report', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('patient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='userreports', to=orm['auth.User'])),
            ('appointment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='appointmentreports', to=orm['consulting.Appointment'])),
            ('kind', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('observations', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('recommendations_treatment', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('consulting', ['Report'])

        # Adding model 'Appointment'
        db.create_table('consulting_appointment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('patient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='patientappointments', to=orm['auth.User'])),
            ('doctor', self.gf('django.db.models.fields.related.ForeignKey')(related_name='doctorappointments', to=orm['auth.User'])),
            ('questionnaire', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='questionnaireappointments', null=True, to=orm['consulting.Questionnaire'])),
            ('treatment', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='treatmentappointments', null=True, to=orm['consulting.Treatment'])),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('hour', self.gf('django.db.models.fields.TimeField')()),
        ))
        db.send_create_signal('consulting', ['Appointment'])

        # Adding M2M table for field answers on 'Appointment'
        db.create_table('consulting_appointment_answers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('appointment', models.ForeignKey(orm['consulting.appointment'], null=False)),
            ('answer', models.ForeignKey(orm['consulting.answer'], null=False))
        ))
        db.create_unique('consulting_appointment_answers', ['appointment_id', 'answer_id'])

        # Adding model 'Questionnaire'
        db.create_table('consulting_questionnaire', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('survey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='questionnaires', to=orm['survey.Survey'])),
            ('self_administered', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('start_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('end_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('from_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('to_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('rate', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('completed', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('consulting', ['Questionnaire'])

        # Adding model 'Answer'
        db.create_table('consulting_answer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('option', self.gf('django.db.models.fields.related.ForeignKey')(related_name='answers', to=orm['survey.Option'])),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('consulting', ['Answer'])

        # Adding model 'Treatment'
        db.create_table('consulting_treatment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('patient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='patienttreatments', to=orm['auth.User'])),
            ('from_appointment', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('consulting', ['Treatment'])

        # Adding model 'Prescription'
        db.create_table('consulting_prescription', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('treatment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='treatmentprescriptions', to=orm['consulting.Treatment'])),
            ('component', self.gf('django.db.models.fields.related.ForeignKey')(related_name='componentprescriptions', to=orm['medicament.Component'])),
            ('before_after', self.gf('django.db.models.fields.IntegerField')()),
            ('months', self.gf('django.db.models.fields.IntegerField')()),
            ('posology', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('consulting', ['Prescription'])


    def backwards(self, orm):
        
        # Deleting model 'Report'
        db.delete_table('consulting_report')

        # Deleting model 'Appointment'
        db.delete_table('consulting_appointment')

        # Removing M2M table for field answers on 'Appointment'
        db.delete_table('consulting_appointment_answers')

        # Deleting model 'Questionnaire'
        db.delete_table('consulting_questionnaire')

        # Deleting model 'Answer'
        db.delete_table('consulting_answer')

        # Deleting model 'Treatment'
        db.delete_table('consulting_treatment')

        # Deleting model 'Prescription'
        db.delete_table('consulting_prescription')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'consulting.answer': {
            'Meta': {'object_name': 'Answer'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'option': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'answers'", 'to': "orm['survey.Option']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'consulting.appointment': {
            'Meta': {'object_name': 'Appointment'},
            'answers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'answerappointments'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['consulting.Answer']"}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'doctor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'doctorappointments'", 'to': "orm['auth.User']"}),
            'hour': ('django.db.models.fields.TimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'patientappointments'", 'to': "orm['auth.User']"}),
            'questionnaire': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'questionnaireappointments'", 'null': 'True', 'to': "orm['consulting.Questionnaire']"}),
            'treatment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'treatmentappointments'", 'null': 'True', 'to': "orm['consulting.Treatment']"})
        },
        'consulting.prescription': {
            'Meta': {'object_name': 'Prescription'},
            'before_after': ('django.db.models.fields.IntegerField', [], {}),
            'component': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'componentprescriptions'", 'to': "orm['medicament.Component']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'months': ('django.db.models.fields.IntegerField', [], {}),
            'posology': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'treatment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'treatmentprescriptions'", 'to': "orm['consulting.Treatment']"})
        },
        'consulting.questionnaire': {
            'Meta': {'object_name': 'Questionnaire'},
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'from_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rate': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'self_administered': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'survey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'questionnaires'", 'to': "orm['survey.Survey']"}),
            'to_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'})
        },
        'consulting.report': {
            'Meta': {'object_name': 'Report'},
            'appointment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'appointmentreports'", 'to': "orm['consulting.Appointment']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'observations': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userreports'", 'to': "orm['auth.User']"}),
            'recommendations_treatment': ('django.db.models.fields.TextField', [], {'blank': 'True'})
        },
        'consulting.treatment': {
            'Meta': {'object_name': 'Treatment'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'from_appointment': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'patienttreatments'", 'to': "orm['auth.User']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'formula.dimension': {
            'Meta': {'object_name': 'Dimension'},
            'factor': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'polynomial': ('django.db.models.fields.TextField', [], {})
        },
        'formula.formula': {
            'Meta': {'object_name': 'Formula'},
            'factor': ('django.db.models.fields.DecimalField', [], {'max_digits': '12', 'decimal_places': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'polynomial': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'sibling': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'siblingformulas'", 'null': 'True', 'to': "orm['formula.Formula']"}),
            'variable': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'variableformulas'", 'to': "orm['formula.Variable']"})
        },
        'formula.variable': {
            'Meta': {'object_name': 'Variable'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'dimension': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'variables'", 'to': "orm['formula.Dimension']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'})
        },
        'medicament.component': {
            'Meta': {'object_name': 'Component'},
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'groupcomponents'", 'symmetrical': 'False', 'to': "orm['medicament.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind_component': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'medicament.group': {
            'Meta': {'object_name': 'Group'},
            'adverse_reaction': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'})
        },
        'survey.block': {
            'Meta': {'object_name': 'Block'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'categoriesblocks'", 'symmetrical': 'False', 'to': "orm['survey.Category']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'formulas': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'formulasblocks'", 'symmetrical': 'False', 'to': "orm['formula.Formula']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'survey.category': {
            'Meta': {'object_name': 'Category'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '15'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'survey.option': {
            'Meta': {'object_name': 'Option'},
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'father': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'fatheroptions'", 'null': 'True', 'to': "orm['survey.Option']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.IntegerField', [], {}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'options'", 'to': "orm['survey.Question']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'weight': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '5', 'decimal_places': '2', 'blank': 'True'})
        },
        'survey.question': {
            'Meta': {'object_name': 'Question'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'questions'", 'symmetrical': 'False', 'to': "orm['survey.Category']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '500'})
        },
        'survey.survey': {
            'Meta': {'object_name': 'Survey'},
            'blocks': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'surveys'", 'symmetrical': 'False', 'to': "orm['survey.Block']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['consulting']
