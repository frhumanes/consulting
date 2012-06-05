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

        # Adding M2M table for field formulas on 'Block'
        db.create_table('survey_block_formulas', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('block', models.ForeignKey(orm['survey.block'], null=False)),
            ('formula', models.ForeignKey(orm['formula.formula'], null=False))
        ))
        db.create_unique('survey_block_formulas', ['block_id', 'formula_id'])

        # Adding model 'Question'
        db.create_table('survey_question', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=500)),
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
            ('father', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='fatheroptions', null=True, to=orm['survey.Option'])),
            ('kind', self.gf('django.db.models.fields.IntegerField')()),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=10)),
            ('weight', self.gf('django.db.models.fields.DecimalField')(null=True, max_digits=5, decimal_places=2, blank=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('survey', ['Option'])


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

        # Removing M2M table for field formulas on 'Block'
        db.delete_table('survey_block_formulas')

        # Deleting model 'Question'
        db.delete_table('survey_question')

        # Removing M2M table for field categories on 'Question'
        db.delete_table('survey_question_categories')

        # Deleting model 'Option'
        db.delete_table('survey_option')


    models = {
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

    complete_apps = ['survey']
