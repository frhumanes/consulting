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
            ('visit', self.gf('django.db.models.fields.related.ForeignKey')(related_name='visitreports', to=orm['consulting.Visit'])),
            ('kind', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('observations', self.gf('django.db.models.fields.TextField')(blank=True)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('consulting', ['Report'])

        # Adding model 'Visit'
        db.create_table('consulting_visit', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('patient', self.gf('django.db.models.fields.related.ForeignKey')(related_name='patientvisits', to=orm['auth.User'])),
            ('doctor', self.gf('django.db.models.fields.related.ForeignKey')(related_name='doctorvisits', to=orm['auth.User'])),
            ('questionnaire', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='questionnairevisits', null=True, to=orm['consulting.Questionnaire'])),
            ('treatment', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='treatmentvisits', null=True, to=orm['consulting.Treatment'])),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('consulting', ['Visit'])

        # Adding M2M table for field answers on 'Visit'
        db.create_table('consulting_visit_answers', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('visit', models.ForeignKey(orm['consulting.visit'], null=False)),
            ('answer', models.ForeignKey(orm['consulting.answer'], null=False))
        ))
        db.create_unique('consulting_visit_answers', ['visit_id', 'answer_id'])

        # Adding model 'Questionnaire'
        db.create_table('consulting_questionnaire', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('survey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='questionnaires', to=orm['survey.Survey'])),
            ('self_administered', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('start_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('end_date', self.gf('django.db.models.fields.DateTimeField')(null=True, blank=True)),
            ('deadline', self.gf('django.db.models.fields.DateTimeField')()),
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
            ('from_visit', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('date', self.gf('django.db.models.fields.DateTimeField')()),
        ))
        db.send_create_signal('consulting', ['Treatment'])

        # Adding M2M table for field medications on 'Treatment'
        db.create_table('consulting_treatment_medications', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('treatment', models.ForeignKey(orm['consulting.treatment'], null=False)),
            ('medication', models.ForeignKey(orm['consulting.medication'], null=False))
        ))
        db.create_unique('consulting_treatment_medications', ['treatment_id', 'medication_id'])

        # Adding model 'Medication'
        db.create_table('consulting_medication', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('medicine', self.gf('django.db.models.fields.related.ForeignKey')(related_name='medications', unique=True, to=orm['medicament.Medicine'])),
            ('posology', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('time', self.gf('django.db.models.fields.IntegerField')()),
            ('before_after', self.gf('django.db.models.fields.CharField')(max_length=9)),
        ))
        db.send_create_signal('consulting', ['Medication'])


    def backwards(self, orm):
        
        # Deleting model 'Report'
        db.delete_table('consulting_report')

        # Deleting model 'Visit'
        db.delete_table('consulting_visit')

        # Removing M2M table for field answers on 'Visit'
        db.delete_table('consulting_visit_answers')

        # Deleting model 'Questionnaire'
        db.delete_table('consulting_questionnaire')

        # Deleting model 'Answer'
        db.delete_table('consulting_answer')

        # Deleting model 'Treatment'
        db.delete_table('consulting_treatment')

        # Removing M2M table for field medications on 'Treatment'
        db.delete_table('consulting_treatment_medications')

        # Deleting model 'Medication'
        db.delete_table('consulting_medication')


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
        'consulting.medication': {
            'Meta': {'object_name': 'Medication'},
            'before_after': ('django.db.models.fields.CharField', [], {'max_length': '9'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'medicine': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'medications'", 'unique': 'True', 'to': "orm['medicament.Medicine']"}),
            'posology': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'time': ('django.db.models.fields.IntegerField', [], {})
        },
        'consulting.questionnaire': {
            'Meta': {'object_name': 'Questionnaire'},
            'completed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {}),
            'deadline': ('django.db.models.fields.DateTimeField', [], {}),
            'end_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rate': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'self_administered': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'start_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True', 'blank': 'True'}),
            'survey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'questionnaires'", 'to': "orm['survey.Survey']"})
        },
        'consulting.report': {
            'Meta': {'object_name': 'Report'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'observations': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'userreports'", 'to': "orm['auth.User']"}),
            'visit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'visitreports'", 'to': "orm['consulting.Visit']"})
        },
        'consulting.treatment': {
            'Meta': {'object_name': 'Treatment'},
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'from_visit': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'medications': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'medicationstreatments'", 'symmetrical': 'False', 'to': "orm['consulting.Medication']"}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'patienttreatments'", 'to': "orm['auth.User']"})
        },
        'consulting.visit': {
            'Meta': {'object_name': 'Visit'},
            'answers': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'answervisits'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['consulting.Answer']"}),
            'date': ('django.db.models.fields.DateTimeField', [], {}),
            'doctor': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'doctorvisits'", 'to': "orm['auth.User']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'patient': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'patientvisits'", 'to': "orm['auth.User']"}),
            'questionnaire': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'questionnairevisits'", 'null': 'True', 'to': "orm['consulting.Questionnaire']"}),
            'treatment': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'treatmentvisits'", 'null': 'True', 'to': "orm['consulting.Treatment']"})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'medicament.group': {
            'Meta': {'object_name': 'Group'},
            'adverse_reaction': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'})
        },
        'medicament.medicine': {
            'Meta': {'object_name': 'Medicine'},
            'active_ingredient': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'medicines'", 'to': "orm['medicament.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '40'})
        },
        'survey.block': {
            'Meta': {'object_name': 'Block'},
            'categories': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'blocks'", 'symmetrical': 'False', 'to': "orm['survey.Category']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
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
            'children': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'children_rel_+'", 'null': 'True', 'to': "orm['survey.Option']"}),
            'code': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
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
            'text': ('django.db.models.fields.CharField', [], {'max_length': '255'})
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
