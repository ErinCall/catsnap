from __future__ import unicode_literals

from functools import wraps
from mock import Mock, MagicMock, patch
import tempfile
from sqlalchemy import create_engine
import sqlalchemy.exc
import time
import subprocess
import os
import os.path
import catsnap

if 'CATSNAP_CELERY_BROKER_URL' not in os.environ:
    os.environ['CATSNAP_CELERY_BROKER_URL'] = 'memory://'

from catsnap.web import app

class TestCase(object):
    def setUp(self):
        (creds_fd, creds) = tempfile.mkstemp()
        self.creds_tempfile = creds
        self.creds_temp_fd = creds_fd
        (config_fd, config) = tempfile.mkstemp()
        self.config_tempfile = config
        self.config_temp_fd = config_fd
        catsnap.config.file_config._input = MagicMock()
        catsnap.config.file_config.CONFIG_FILE = config
        catsnap.config.file_config.LEGACY_CREDENTIALS_FILE = creds

        catsnap.config.argument_config.sys = MagicMock()

        catsnap.config.file_config.getpass = MagicMock()

        catsnap.Client()._engine = db_info['engine']
        catsnap.Client().session().commit = catsnap.Client().session().flush

        app.config['TESTING'] = True
        app.secret_key = str('super sekrit')
        self.app = app.test_client()

    def tearDown(self):
        os.close(self.creds_temp_fd)
        os.close(self.config_temp_fd)
        catsnap.config.MetaConfig._instance = None
        catsnap.Client().session().rollback()
        catsnap.Client._instance = None

db_info = {}

def setUpPackage():
    create_temp_database()
    temp_db_url = 'postgresql://localhost/%s' % db_info['temp_db_name']
    db_info['engine'] = create_engine(temp_db_url)

    apply_migrations(temp_db_url)

def tearDownPackage():
    terminate_query = """
        select pg_terminate_backend( %(pid_column)s )
        from pg_stat_activity
        where datname = '%(db_name)s'
    """
    try:
        db_info['master_engine'].execute(terminate_query % {
            'pid_column': 'procpid',
            'db_name': db_info['temp_db_name'],
        })
    except sqlalchemy.exc.ProgrammingError as e:
        if '"procpid" does not exist' in str(e):
            #postgres 9.2 changed pg_stat_activity.procpid to just .pid
            db_info['master_engine'].execute(terminate_query % {
                'pid_column': 'pid',
                'db_name': db_info['temp_db_name'],
            })
        else:
            raise
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

def with_settings(**settings):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            with patch('catsnap.config.env_config.os.environ', {}) as env:
                for key, value in settings.iteritems():
                    env['CATSNAP_' + key.upper()] = value
                fn(*args, **kwargs)
        return wrapper
    return decorator

def logged_in(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        with patch('catsnap.web.utils.g', Mock()) as mock_g:
            fn(*args, **kwargs)
    return wrapper

