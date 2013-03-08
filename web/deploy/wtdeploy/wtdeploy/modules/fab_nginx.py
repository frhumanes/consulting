#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# author: antonio hinojo

from fabric.api import sudo
from fabric.api import cd
from fabric.api import run
from fabric.api import env
from fabric.contrib.files import upload_template
from fabric.contrib.files import exists


def install(conf_folder):
    sudo("apt-get -y install nginx")


def copy_conf_files(conf_folder, deploy_folder, is_mobile):
    with cd(deploy_folder):
        run('mkdir -p nginx')

        if is_mobile:
            #nginx stuff
            upload_template('%s/nginx/host_conf_mobile' % conf_folder, 'nginx', context=env)
            sudo('cp nginx/host_conf_mobile /etc/nginx/sites-available/%(host)s' % env)

            #apache stuff
            if exists('%s/apache/apache' % conf_folder):
                upload_template('%s/apache/apache_mobile' % conf_folder, 'apache2', context=env)
                sudo('cp apache2/apache_mobile /etc/apache2/sites-available/%(host)s' % env)

            #symbolic link to main app media
            if exists('%(deploy_folder)s/app/media' % env):
                   sudo('rm -rvf %(deploy_folder)s/app/media' % env)
            sudo('ln -fs %(main_app_deploy_folder)s/app/media %(deploy_folder)s/app/media' % env)
        else:
            #nginx stuff
            upload_template('%s/nginx/host_conf' % conf_folder, 'nginx', context=env)
            upload_template('%s/nginx/nginx.conf' % conf_folder, 'nginx', context=env)
            upload_template('%s/nginx/proxy.conf' % conf_folder, 'nginx', context=env)

            sudo('cp nginx/host_conf /etc/nginx/sites-available/%(host)s' % env)
            sudo('cp nginx/nginx.conf /etc/nginx/nginx.conf')
            sudo('cp nginx/proxy.conf /etc/nginx/proxy.conf')

            #apache stuff
            if exists('%s/apache/apache' % conf_folder):
                upload_template('%s/apache/apache' % conf_folder, 'apache2', context=env)
                sudo('cp apache2/apache /etc/apache2/sites-available/%(host)s' % env)
                sudo('chmod a+r /etc/apache2/sites-available/%(host)s' % env)


        if not exists('/etc/nginx/sites-enabled/%(host)s' % env):
            sudo('ln -fs /etc/nginx/sites-available/%(host)s /etc/nginx/sites-enabled/%(host)s' % env)
            sudo('chmod a+r /etc/nginx/sites-enabled/%(host)s' % env)
           

        if exists('%s/apache/apache' % conf_folder) and not exists('/etc/apache2/sites-enabled/%(host)s' % env):
            sudo('ln -fs /etc/apache2/sites-available/%(host)s /etc/apache2/sites-enabled/%(host)s' % env)
            sudo('chmod a+r /etc/apache2/sites-enabled/%(host)s' % env)


def start():
    sudo("/etc/init.d/nginx start")


def stop():
    sudo("/etc/init.d/nginx stop")


def restart():
    sudo("/etc/init.d/nginx restart")

