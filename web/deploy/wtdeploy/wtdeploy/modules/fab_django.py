#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# author: javi santana

from fabric.api import *
from fabric.contrib.files import upload_template
from fabric.contrib.files import exists

import os.path
import tempfile

import fab_python


def svn_checkout(to_dir):
    """ checkout svn repository into dir """
    cmd = "svn co --non-interactive --no-auth-cache --trust-server-cert --username %(repo_user)s --password %(repo_password)s %(repo)s" % env
    cmd = cmd + " " + to_dir
    run(cmd)

def install(conf_folder):
    pass

def copy_conf_files(conf_folder, project_dir, is_mobile=False):
    put('%s/django/app.wsgi' % conf_folder, project_dir)
    upload_template('%s/django/local_settings.py' % conf_folder, project_dir + "/app", context=env)
    if is_mobile:
        put('%s/django/mobile_local_settings.py' % conf_folder, project_dir + "/app")

def create_virtualenv(conf_folder, project_dir):
    req_file = '%s/django/requirements.txt' % conf_folder
    # if project has own req file upload
    if(os.path.exists(req_file)):
        put(req_file, project_dir)
    else:
        put('%s/requirements.txt' % env.source_folder, project_dir)

    fab_python.create_virtualenv(project_dir + "/requirements.txt", "env", project_dir)

def prepare_env(conf_folder, project_dir):
    create_virtualenv(conf_folder, project_dir)
    with cd(project_dir):
        if env.from_repo:
            svn_checkout("app")
        else:
            tmpfile = tempfile.mktemp()
            local("cd %s && tar -czf %s.tar.gz ." % (env.source_folder, tmpfile))
            put('%s.tar.gz' % tmpfile , '/tmp/%s.tar.gz' % env.app_name)
            run("mkdir -p app")
            run('tar -xzf /tmp/%s.tar.gz -C app' % env.app_name)
        run("mkdir -p logs")

def syncdb():
    # make a dump to avoid problems
    run("mysqldump -u%(database_admin)s -p%(database_admin_pass)s %(database_name)s > dump_%(database_name)s.sql" % env)
    run('source env/bin/activate && python app/manage.py syncdb --noinput')
    #run('source env/bin/activate && python app/manage.py migrate')

def update_index():
    run('source env/bin/activate && python app/manage.py update_index')

def load_fixture(fixture_file):
    run("source env/bin/activate && python app/manage.py loaddata %s" % fixture_file)

def deploy():
    if env.from_repo:
        cmd = "svn up --username %(repo_user)s --password %(repo_password)s app" % env
        run(cmd)
    else:
        tmpfile = tempfile.mktemp()
        local("cd %s && tar -czf %s.tar.gz ." % (env.source_folder, tmpfile))
        put('%s.tar.gz' % tmpfile , '/tmp/%s.tar.gz' % env.app_name)
        run("mkdir -p app")
        run('tar -xzf /tmp/%s.tar.gz -C app' % env.app_name)
    

def create_admin():
    cmd = "from django.contrib.auth.models import User; User.objects.create_superuser('admin', 'admin@wtelecom.es', '%s')" % env.admin_password
    run('source env/bin/activate && echo "' + cmd + '" | python app/manage.py shell')

def run_django_cmd(cmd):
    run('source env/bin/activate && python app/manage.py syncdb --noinput')

def compile_locales():
    with cd(env.deploy_folder):
        run('source env/bin/activate && cd app/ && django-admin.py compilemessages')

def start():
    pass

def stop():
    pass

def restart():
    run("touch app.wsgi")

def clean_pyc():
    sudo('find . -name "*.pyc" -delete')
    run('source env/bin/activate && python app/manage.py clean_pyc')

def restart_app(app_name):
    sudo('supervisorctl restart %s' % app_name)

def load_data(data):
    """ load application fixtures"""
    for k, v in data.items():
        for fixture in v:
            if k:
                run("source env/bin/activate && python app/manage.py loaddata app/%s/fixtures/%s.json" %(k, fixture))
            else:
                load_fixture(fixture)
