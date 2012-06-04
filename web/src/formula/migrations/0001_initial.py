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
            ('variable', self.gf('django.db.models.fields.related.ForeignKey')(related_name='variableformulas', to=orm['formula.Variable'])),
            ('sibling', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='siblingformulas', null=True, to=orm['formula.Formula'])),
            ('polynomial', self.gf('django.db.models.fields.CharField')(max_length=250)),
            ('factor', self.gf('django.db.models.fields.DecimalField')(max_digits=12, decimal_places=10)),
        ))
        db.send_create_signal('formula', ['Formula'])


    def backwards(self, orm):
        
        # Deleting model 'Dimension'
        db.delete_table('formula_dimension')

        # Deleting model 'Variable'
        db.delete_table('formula_variable')

        # Deleting model 'Formula'
        db.delete_table('formula_formula')


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
        }
    }

    complete_apps = ['formula']
