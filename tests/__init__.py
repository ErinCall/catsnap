from __future__ import unicode_literals

from mock import MagicMock
import tempfile
from sqlalchemy import create_engine
import time
import subprocess
import os.path

import catsnap
from catsnap import Client
import catsnap.config.file_config

class TestCase():
    def setUp(self):
        (_, creds) = tempfile.mkstemp()
        self.creds_tempfile = creds
        (_, config) = tempfile.mkstemp()
        self.config_tempfile = config
        catsnap.config.file_config._input = MagicMock()
        catsnap.config.file_config.CONFIG_FILE = config
        catsnap.config.file_config.LEGACY_CREDENTIALS_FILE = creds

        catsnap.config.argument_config.sys = MagicMock()

        catsnap.config.file_config.getpass = MagicMock()

        Client()._engine = db_info['engine']

    def tearDown(self):
        catsnap.config.MetaConfig._instance = None
        Client().session().rollback()
        catsnap.Client._instance = None

db_info = {}

def setUpPackage():
    create_temp_database()
    temp_db_url = 'postgresql://localhost/%s' % db_info['temp_db_name']
    db_info['engine'] = create_engine(temp_db_url)

    apply_migrations(temp_db_url)

def tearDownPackage():
    db_info['master_engine'].execute("""
        select pg_terminate_backend( procpid )
        from pg_stat_activity
        where datname = '%s'
    """ % db_info['temp_db_name'])
    drop_temp_database()

def create_temp_database():
    db_info['master_engine'] = create_engine('postgresql://localhost/postgres')
    db_info['temp_db_name'] = 'catsnap_test_%d' % int(time.time())
    conn = db_info['master_engine'].connect()
    conn.execute('commit')#work around sqlalchemy's auto-transactions
    conn.execute('create database %s' % db_info['temp_db_name'])

def drop_temp_database():
    conn = db_info['master_engine'].connect()
    conn.execute('commit')
    conn.execute('drop database %s' % db_info['temp_db_name'])

def apply_migrations(temp_db_url):
    migrations_dir = os.path.join(os.path.dirname(__file__), '..', 'migrations')
    subprocess.check_output(['yoyo-migrate', '-b', 'apply', migrations_dir, temp_db_url])

