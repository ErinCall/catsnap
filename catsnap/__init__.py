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

class Config(object):

    CREDENTIALS_FILE = os.path.join(os.environ['HOME'], '.boto')
    CONFIG_FILE = os.path.join(os.environ['HOME'], '.catsnap')
    parser = None

    _instance = None
    _tables = {}
    _bucket = None

    _dynamo_connection = None
    _s3_connection = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Config, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self, get_missing_settings=True):
        self.parser = ConfigParser.ConfigParser()
        self.parser.read([self.CREDENTIALS_FILE, self.CONFIG_FILE])

        if get_missing_settings:
            self.get_settings()

    def get_settings(self, override_existing=False):
        missing_creds = False
        missing_config = False
        try:
            self.parser.get('Credentials', 'aws_access_key_id')
            self.parser.get('Credentials', 'aws_secret_access_key')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            missing_creds = True
        if override_existing or missing_creds:
            self.get_credentials(override_existing=override_existing)

        try:
            self.parser.get('catsnap', 'bucket')
            self.parser.get('catsnap', 'table_prefix')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            missing_config = True
        if override_existing or missing_config:
            self.get_config(override_existing=override_existing)

        with open(self.CONFIG_FILE, 'w', 600) as config_file:
            self.parser.write(config_file)

    def get_credentials(self, override_existing=False):
        sys.stdout.write("Find your credentials at https://portal.aws.amazon.com/"
                         "gp/aws/securityCredentials\n")
        if not self.parser.has_section('Credentials'):
            self.parser.add_section('Credentials')

        has_key_id = self.parser.has_option('Credentials', 'aws_access_key_id')
        has_secret_key = self.parser.has_option('Credentials',
                'aws_secret_access_key')
        if override_existing or not has_key_id:
            use_default = ''
            if has_key_id:
                use_default = " (leave blank to keep using '%s')" % \
                        self.parser.get('Credentials', 'aws_access_key_id')
            key_id = self._input('Enter your access key id%s: ' % use_default)
            if has_key_id and not key_id:
                key_id = self.parser.get('Credentials', 'aws_access_key_id')
            self.parser.set('Credentials', 'aws_access_key_id', key_id)

        if override_existing or not has_secret_key:
            use_default = ''
            if has_secret_key:
                use_default = " (leave blank to keep using what you had before)"
            secret_key = getpass.getpass('Enter your secret access key%s: '
                        % use_default)
            if has_secret_key and not secret_key:
                secret_key = self.parser.get('Credentials',
                        'aws_secret_access_key')
            self.parser.set('Credentials', 'aws_secret_access_key', secret_key)

    def get_config(self, override_existing=False):
        if not self.parser.has_section('catsnap'):
            self.parser.add_section('catsnap')

        has_bucket = self.parser.has_option('catsnap', 'bucket')
        has_custom_prefix =  has_bucket \
                and self.parser.has_option('catsnap', 'table_prefix') \
                and self.parser.get('catsnap', 'bucket') != \
                        self.parser.get('catsnap', 'table_prefix')
        if override_existing or not has_bucket:
            bucket_name = '%s-%s' % (BUCKET_BASE, os.environ['USER'])
            use = 'use'
            if has_bucket:
                bucket_name = self.parser.get('catsnap', 'bucket')
                use = 'keep using'
            actual_bucket_name = self._input("Please name your bucket (leave "
                    "blank to %(use)s '%(bucket_name)s'): " % {
                        'use': use, 'bucket_name': bucket_name})
            self.parser.set('catsnap', 'bucket', actual_bucket_name or bucket_name)

        if not has_custom_prefix:
            self.parser.set('catsnap', 'table_prefix',
                    self.parser.get('catsnap', 'bucket'))

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
            bucket_name = self.bucket_name()
            s3 = self.get_s3()
            all_buckets = [x.name for x in s3.get_all_buckets()]
            if bucket_name not in all_buckets:
                self._bucket = s3.create_bucket(bucket_name)
            else:
                self._bucket = s3.get_bucket(bucket_name)
        return self._bucket

    def create_table(self, table_name):
        table_prefix = self._table_prefix()
        table_name = '%s-%s' % (table_prefix, table_name)

        dynamo = self.get_dynamodb()
        schema = dynamo.create_schema(hash_key_name='tag',
                hash_key_proto_value='S')
        return dynamo.create_table(name=table_name,
                schema=schema,
                read_units=3,
                write_units=5)

    def table(self, table_name):
        table_prefix = self._table_prefix()
        table_name = '%s-%s' % (table_prefix, table_name)

        if table_name not in self._tables:
            dynamo = self.get_dynamodb()
            self._tables[table_name] = dynamo.get_table(table_name)
        return self._tables[table_name]

    def get_dynamodb(self):
        if not self._dynamo_connection:
            self._dynamo_connection = boto.connect_dynamodb(
                    aws_access_key_id=self._access_key_id(),
                    aws_secret_access_key=self._secret_access_key())
        return self._dynamo_connection

    def get_s3(self):
        if not self._s3_connection:
            self._s3_connection = boto.connect_s3(
                    aws_access_key_id=self._access_key_id(),
                    aws_secret_access_key=self._secret_access_key())
        return self._s3_connection

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
