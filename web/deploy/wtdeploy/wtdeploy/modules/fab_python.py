#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# author: javi santana

from fabric.api import *
from fabric.contrib.files import upload_template
from fabric.contrib.files import exists

def install(conf_folder):
   sudo("apt-get -y install python python-setuptools")
   sudo("easy_install pip")
   sudo("pip install virtualenv")

def create_virtualenv(requirements_file, name, dest_dir):
    with cd(dest_dir):
        pip_version = run("pip --version | cut -d' ' -f2")
        if pip_version <= "1.0.2":
            run("pip install -E %s -r %s" % (name, requirements_file))
        else:
            run('virtualenv --clear --no-site-packages %s' % name)
            run("%s/bin/pip install -r %s" % (name, requirements_file))
