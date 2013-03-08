#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# author: fernando ruiz

from fabric.api import *
from fabric.contrib.files import upload_template
from fabric.contrib.files import exists

def install(conf_folder):
   sudo("apt-get -y install supervisor")

def copy_conf_files(conf_folder, deploy_folder):
    with cd(deploy_folder):
        run('mkdir -p supervisor')

        upload_template('%s/supervisor/supervisor' % conf_folder, 'supervisor', context=env)
        sudo('cp supervisor/supervisor /etc/supervisor/conf.d/%(host)s.conf' % env)
        sudo('supervisorctl reload')

