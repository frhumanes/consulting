#!/usr/bin/python
# -*- encoding: utf-8 -*-
#
# author: javi santana

from fabric.api import env
from wtdeploy import push, upgrade_env, update_conf

def development():
    env.app_name = 'consulting'
    env.fixtures_name = {
        None: [ '01_group', '02_component', '06_question',  '07_option', '03_category', '08_dimension', '09_variable', '10_formula', '04_block', '05_survey', '00_illness']
    }
    env.ip = '89.140.10.57'
    env.nginx_serves_static = True

    env.source_folder = 'src'
    env.deploy_folder = "/home/rambot/consulting"
    env.hosts = ['89.140.10.57']
    env.user = 'wtdeploy'
    env.password = 'Rp53*PF[;Zp<E@Qg;ANIICA4[Pmq?pkh'
    env.local_conf_folder = "deploy/89.140.10.57"

    env.repo = "https://svn.squada.com/svn/consulting30/trunk/web/src"
    env.repo_user = 'fruiz'
    env.repo_password = 'Wtelecom123'

    env.database_admin = 'root'
    env.database_admin_pass = 'cmglpa'

    env.database_name = 'consulting'
    env.database_user = 'consulting'
    env.database_pass = 'consulting'

    env.stats_db_name = env.database_name + "_stats"
    env.create_stats_database = False
    env.is_mobile = False
