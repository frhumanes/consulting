#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# author: javi santana

from fabric.api import env
from wtdeploy import push


def development():
    env.app_name = 'consulting'
    env.fixtures_name = {
        'medicament': ['01_group', '02_component'],
        'consulting': ['03_category', '04_block', '05_survey', '06_question'],
    }
    env.ip = '89.140.10.57'
    env.nginx_serves_static = True

    env.deploy_folder = "/home/rambot/consulting"
    env.hosts = ['89.140.10.57']
    env.user = 'rambot'
    env.password = 'ramboFTW'
    env.local_conf_folder = "deploy/89.140.10.57"

    env.repo = "https://intranet.wtelecom.es/svn/consulting30/trunk/web/src"
    env.repo_user = ''
    env.repo_password = ''

    env.database_admin = 'root'
    env.database_admin_pass = 'cmglpa'

    env.database_name = 'consulting'
    env.database_user = 'consulting'
    env.database_pass = 'consulting'

    env.stats_db_name = env.database_name + "_stats"
    env.create_stats_database = False
    env.is_mobile = False
