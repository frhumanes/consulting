# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Survey'
        db.create_table('survey_survey', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('survey', ['Survey'])

        # Adding M2M table for field blocks on 'Survey'
        db.create_table('survey_survey_blocks', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('survey', models.ForeignKey(orm['survey.survey'], null=False)),
            ('block', models.ForeignKey(orm['survey.block'], null=False))
        ))
        db.create_unique('survey_survey_blocks', ['survey_id', 'block_id'])

        # Adding model 'Category'
        db.create_table('survey_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=15)),
        ))
        db.send_create_signal('survey', ['Category'])

        # Adding model 'Block'
        db.create_table('survey_block', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('kind', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('survey', ['Block'])

        # Adding M2M table for field categories on 'Block'
        db.create_table('survey_block_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('block', models.ForeignKey(orm['survey.block'], null=False)),
            ('category', models.ForeignKey(orm['survey.category'], null=False))
        ))
        db.create_unique('survey_block_categories', ['block_id', 'category_id'])

        # Adding model 'Question'
        db.create_table('survey_question', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('survey', ['Question'])

        # Adding M2M table for field categories on 'Question'
        db.create_table('survey_question_categories', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('question', models.ForeignKey(orm['survey.question'], null=False)),
            ('category', models.ForeignKey(orm['survey.category'], null=False))
        ))
        db.create_unique('survey_question_categories', ['question_id', 'category_id'])

        # Adding model 'Option'
        db.create_table('survey_option', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='options', to=orm['survey.Question'])),
            ('kind', self.gf('django.db.models.fields.IntegerField')()),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('weight', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('survey', ['Option'])

        # Adding M2M table for field children on 'Option'
        db.create_table('survey_option_children', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_option', models.ForeignKey(orm['survey.option'], null=False)),
            ('to_option', models.ForeignKey(orm['survey.option'], null=False))
        ))
        db.create_unique('survey_option_children', ['from_option_id', 'to_option_id'])


    def backwards(self, orm):
        
        # Deleting model 'Survey'
        db.delete_table('survey_survey')

        # Removing M2M table for field blocks on 'Survey'
        db.delete_table('survey_survey_blocks')

        # Deleting model 'Category'
        db.delete_table('survey_category')

        # Deleting model 'Block'
        db.delete_table('survey_block')

        # Removing M2M table for field categories on 'Block'
        db.delete_table('survey_block_categories')

        # Deleting model 'Question'
        db.delete_table('survey_question')

        # Removing M2M table for field categories on 'Question'
        db.delete_table('survey_question_categories')

        # Deleting model 'Option'
        db.delete_table('survey_option')

        # Removing M2M table for field children on 'Option'
        db.delete_table('survey_option_children')


    models = {
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

    complete_apps = ['survey']
