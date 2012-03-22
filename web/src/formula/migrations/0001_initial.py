# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Dimension'
        db.create_table('formula_dimension', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('polynomial', self.gf('django.db.models.fields.TextField')()),
            ('factor', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=8)),
        ))
        db.send_create_signal('formula', ['Dimension'])

        # Adding model 'Variable'
        db.create_table('formula_variable', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('dimension', self.gf('django.db.models.fields.related.ForeignKey')(related_name='variables', to=orm['formula.Dimension'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('code', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
        ))
        db.send_create_signal('formula', ['Variable'])

        # Adding model 'Formula'
        db.create_table('formula_formula', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('block', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blockformulas', to=orm['survey.Block'])),
            ('variable', self.gf('django.db.models.fields.related.ForeignKey')(related_name='variableformulas', to=orm['formula.Variable'])),
            ('polynomial', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('factor', self.gf('django.db.models.fields.DecimalField')(max_digits=10, decimal_places=8)),
        ))
        db.send_create_signal('formula', ['Formula'])

        # Adding M2M table for field children on 'Formula'
        db.create_table('formula_formula_children', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('from_formula', models.ForeignKey(orm['formula.formula'], null=False)),
            ('to_formula', models.ForeignKey(orm['formula.formula'], null=False))
        ))
        db.create_unique('formula_formula_children', ['from_formula_id', 'to_formula_id'])


    def backwards(self, orm):
        
        # Deleting model 'Dimension'
        db.delete_table('formula_dimension')

        # Deleting model 'Variable'
        db.delete_table('formula_variable')

        # Deleting model 'Formula'
        db.delete_table('formula_formula')

        # Removing M2M table for field children on 'Formula'
        db.delete_table('formula_formula_children')


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
            'block': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blockformulas'", 'to': "orm['survey.Block']"}),
            'children': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'children_rel_+'", 'null': 'True', 'to': "orm['formula.Formula']"}),
            'factor': ('django.db.models.fields.DecimalField', [], {'max_digits': '10', 'decimal_places': '8'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'polynomial': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
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
        }
    }

    complete_apps = ['formula']
