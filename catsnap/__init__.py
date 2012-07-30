from __future__ import unicode_literals
import os
import sys
import getpass
import boto
import ConfigParser

from catsnap import settings
from boto.exception import DynamoDBResponseError

#This really oughtta be, like, the tablename or something, but I screwed up, so
#now there're existing catsnap installs that use this schema. Sucks :(
#So yeah every table is keyed on an attribute called 'tag'
HASH_KEY = 'tag'
BUCKET_BASE = 'catsnap'

AUTH_SETTINGS = ['aws_access_key_id', 'aws_secret_access_key']
CATSNAP_SETTINGS = ['bucket']
ALL_SETTINGS = AUTH_SETTINGS + CATSNAP_SETTINGS

class Singleton(object):
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(cls, *args, **kwargs)
        return cls._instance

class Config(Singleton):
    CREDENTIALS_FILE = os.path.join(os.environ['HOME'], '.boto')
    CONFIG_FILE = os.path.join(os.environ['HOME'], '.catsnap')
    parser = None

    def __init__(self):
        self.parser = ConfigParser.ConfigParser()
        self.parser.read([self.CREDENTIALS_FILE, self.CONFIG_FILE])

    def get_settings(self, override_existing=False, settings=[]):
        missing_creds = False
        missing_config = False

        if settings == []:
            settings = ALL_SETTINGS
        try:
            for setting in AUTH_SETTINGS:
                self.parser.get('Credentials', setting)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            missing_creds = True
        if override_existing or missing_creds:
            self.get_credentials(settings, override_existing=override_existing)

        try:
            for setting in CATSNAP_SETTINGS:
                self.parser.get('catsnap', setting)
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            missing_config = True
        if override_existing or missing_config:
            self.get_config(settings, override_existing=override_existing)

        with open(self.CONFIG_FILE, 'w', 600) as config_file:
            self.parser.write(config_file)

    def get_credentials(self, settings, override_existing=False):
        sys.stdout.write("Find your credentials at https://portal.aws.amazon.com/"
                         "gp/aws/securityCredentials\n")

        self._get_setting('Credentials', 'aws_access_key_id',
                'Enter your access key id%s: ',
                " (leave blank to keep using '%s')",
                override_existing, self._input, settings)
        self._get_setting('Credentials', 'aws_secret_access_key',
                'Enter your secret access key%s',
                " (leave blank to keep using what you had before)",
                override_existing, getpass.getpass, settings)

    def get_config(self, settings, override_existing=False):
        if not self.parser.has_section('catsnap'):
            self.parser.add_section('catsnap')

        has_custom_prefix =  self.parser.has_option('catsnap', 'bucket') \
                and self.parser.has_option('catsnap', 'table_prefix') \
                and self.parser.get('catsnap', 'bucket') != \
                        self.parser.get('catsnap', 'table_prefix')

        self._get_setting('catsnap', 'bucket',
                "Please name your bucket%s: ",
                " (leave blank to use '%s')",
                override_existing, self._input, settings,
                global_default='%s-%s' % (BUCKET_BASE, os.environ['USER']))

        if not has_custom_prefix:
            self.parser.set('catsnap', 'table_prefix',
                    self.parser.get('catsnap', 'bucket'))

    def _get_setting(self, section, setting_name, message,
                    override_message, override_existing, read,
                    settings, global_default=None):
        if setting_name not in settings:
            return

        if not self.parser.has_section(section):
            self.parser.add_section(section)

        has_setting = self.parser.has_option(section, setting_name)
        if override_existing or not has_setting:
            use_default = ''
            if global_default:
                use_default = override_message % global_default
            if has_setting:
                try:
                    use_default = override_message % \
                            self.parser.get(section, setting_name)
                except TypeError:
                    use_default = override_message
            setting_value = read(message % use_default)
            if has_setting and not setting_value:
                setting_value = self.parser.get(section, setting_name)
            setting_value = setting_value or global_default
            self.parser.set(section, setting_name, setting_value)

    def bucket_name(self):
        return self.parser.get('catsnap', 'bucket')

    def _table_prefix(self):
        return self.parser.get('catsnap', 'table_prefix')

    def _access_key_id(self):
        return self.parser.get('Credentials', 'aws_access_key_id')

    def _secret_access_key(self):
        return self.parser.get('Credentials', 'aws_secret_access_key')

    def _input(self, *args, **kwargs):
        return raw_input(*args, **kwargs)

class Client(Singleton):
    _tables = {}
    _bucket = None

    _dynamo_connection = None
    _s3_connection = None
    config = None

    def __init__(self):
        config = Config()
        config.get_settings()

    def setup(self):
        created_tables = 0
        try:
            self.create_table('tag')
            created_tables += 1
        except DynamoDBResponseError, e:
            if e.error_code != 'ResourceInUseException':
                raise
        try:
            self.create_table('image')
            created_tables += 1
        except DynamoDBResponseError, e:
            if e.error_code != 'ResourceInUseException':
                raise

        return created_tables

    def bucket(self):
        if not self._bucket:
            bucket_name = Config().bucket_name()
            s3 = self.get_s3()
            all_buckets = [x.name for x in s3.get_all_buckets()]
            if bucket_name not in all_buckets:
                self._bucket = s3.create_bucket(bucket_name)
            else:
                self._bucket = s3.get_bucket(bucket_name)
        return self._bucket

    def create_table(self, table_name):
        table_prefix = Config()._table_prefix()
        table_name = '%s-%s' % (table_prefix, table_name)

        dynamo = self.get_dynamodb()
        schema = dynamo.create_schema(hash_key_name='tag',
                hash_key_proto_value='S')
        return dynamo.create_table(name=table_name,
                schema=schema,
                read_units=3,
                write_units=5)

    def table(self, table_name):
        table_prefix = Config()._table_prefix()
        table_name = '%s-%s' % (table_prefix, table_name)

        if table_name not in self._tables:
            dynamo = self.get_dynamodb()
            self._tables[table_name] = dynamo.get_table(table_name)
        return self._tables[table_name]

    def get_dynamodb(self):
        if not self._dynamo_connection:
            self._dynamo_connection = boto.connect_dynamodb(
                    aws_access_key_id=Config()._access_key_id(),
                    aws_secret_access_key=Config()._secret_access_key())
        return self._dynamo_connection

    def get_s3(self):
        if not self._s3_connection:
            self._s3_connection = boto.connect_s3(
                    aws_access_key_id=Config()._access_key_id(),
                    aws_secret_access_key=Config()._secret_access_key())
        return self._s3_connection

