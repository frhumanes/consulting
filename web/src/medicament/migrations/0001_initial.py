# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Group'
        db.create_table('medicament_group', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40, blank=True)),
            ('adverse_reaction', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('medicament', ['Group'])

        # Adding model 'Medicine'
        db.create_table('medicament_medicine', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(related_name='medicines', to=orm['medicament.Group'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=40)),
            ('active_ingredient', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('medicament', ['Medicine'])


    def backwards(self, orm):
        
        # Deleting model 'Group'
        db.delete_table('medicament_group')

        # Deleting model 'Medicine'
        db.delete_table('medicament_medicine')


    models = {
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
        }
    }

    complete_apps = ['medicament']
