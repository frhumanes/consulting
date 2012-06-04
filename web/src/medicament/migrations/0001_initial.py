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

        # Adding model 'Component'
        db.create_table('medicament_component', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('kind_component', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
        ))
        db.send_create_signal('medicament', ['Component'])

        # Adding M2M table for field groups on 'Component'
        db.create_table('medicament_component_groups', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('component', models.ForeignKey(orm['medicament.component'], null=False)),
            ('group', models.ForeignKey(orm['medicament.group'], null=False))
        ))
        db.create_unique('medicament_component_groups', ['component_id', 'group_id'])


    def backwards(self, orm):
        
        # Deleting model 'Group'
        db.delete_table('medicament_group')

        # Deleting model 'Component'
        db.delete_table('medicament_component')

        # Removing M2M table for field groups on 'Component'
        db.delete_table('medicament_component_groups')


    models = {
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
        }
    }

    complete_apps = ['medicament']
