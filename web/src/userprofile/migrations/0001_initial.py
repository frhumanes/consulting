# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Profile'
        db.create_table('userprofile_profile', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], unique=True)),
            ('doctor', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='doctor', null=True, to=orm['auth.User'])),
            ('search_field', self.gf('django.db.models.fields.CharField')(max_length=200, blank=True)),
            ('username', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('first_surname', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('second_surname', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('nif', self.gf('django.db.models.fields.CharField')(max_length=9, blank=True)),
            ('sex', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('address', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('town', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('postcode', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('dob', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('status', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('phone1', self.gf('django.db.models.fields.CharField')(max_length=9, blank=True)),
            ('phone2', self.gf('django.db.models.fields.CharField')(max_length=9, blank=True)),
            ('email', self.gf('django.db.models.fields.EmailField')(max_length=150, blank=True)),
            ('profession', self.gf('django.db.models.fields.CharField')(max_length=150, blank=True)),
            ('role', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('userprofile', ['Profile'])

        # Adding M2M table for field patients on 'Profile'
        db.create_table('userprofile_profile_patients', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('profile', models.ForeignKey(orm['userprofile.profile'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('userprofile_profile_patients', ['profile_id', 'user_id'])


    def backwards(self, orm):
        
        # Deleting model 'Profile'
        db.delete_table('userprofile_profile')

        # Removing M2M table for field patients on 'Profile'
        db.delete_table('userprofile_profile_patients')


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
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'userprofile.profile': {
            'Meta': {'object_name': 'Profile'},
            'address': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'dob': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'doctor': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'doctor'", 'null': 'True', 'to': "orm['auth.User']"}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '150', 'blank': 'True'}),
            'first_surname': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'nif': ('django.db.models.fields.CharField', [], {'max_length': '9', 'blank': 'True'}),
            'patients': ('django.db.models.fields.related.ManyToManyField', [], {'blank': 'True', 'related_name': "'patients'", 'null': 'True', 'symmetrical': 'False', 'to': "orm['auth.User']"}),
            'phone1': ('django.db.models.fields.CharField', [], {'max_length': '9', 'blank': 'True'}),
            'phone2': ('django.db.models.fields.CharField', [], {'max_length': '9', 'blank': 'True'}),
            'postcode': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'profession': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'role': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'search_field': ('django.db.models.fields.CharField', [], {'max_length': '200', 'blank': 'True'}),
            'second_surname': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'sex': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'status': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'town': ('django.db.models.fields.CharField', [], {'max_length': '150', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'unique': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        }
    }

    complete_apps = ['userprofile']
