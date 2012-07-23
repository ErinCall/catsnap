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

    def __init__(self):
        self.parser = ConfigParser.ConfigParser()
        self.parser.read([self.CREDENTIALS_FILE, self.CONFIG_FILE])

        try:
            self.parser.get('Credentials', 'aws_access_key_id')
            self.parser.get('Credentials', 'aws_secret_access_key')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            self.get_credentials()

        try:
            self.parser.get('catsnap', 'bucket')
            self.parser.get('catsnap', 'table_prefix')
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            self.get_config()

        with open(self.CONFIG_FILE, 'w', 600) as config_file:
            self.parser.write(config_file)

    def get_credentials(self):
        sys.stdout.write("Find your credentials at https://portal.aws.amazon.com/"
                         "gp/aws/securityCredentials\n")
        if not self.parser.has_section('Credentials'):
            self.parser.add_section('Credentials')
        if not self.parser.has_option('Credentials', 'aws_access_key_id'):
            self.parser.set('Credentials', 'aws_access_key_id',
                    self._input('Enter your access key id: '))
        if not self.parser.has_option('Credentials', 'aws_secret_access_key'):
            self.parser.set('Credentials', 'aws_secret_access_key',
                    getpass.getpass('Enter your secret access key: '))

    def get_config(self):
        if not self.parser.has_section('catsnap'):
            self.parser.add_section('catsnap')
        if not self.parser.has_option('catsnap', 'bucket'):
            bucket_name = '%s-%s' % (settings.BUCKET_BASE, os.environ['USER'])
            actual_bucket_name = self._input("Please name your bucket (leave "
                    "blank to use '%s'): " % bucket_name)
            self.parser.set('catsnap', 'bucket', actual_bucket_name or bucket_name)

        if not self.parser.has_option('catsnap', 'table_prefix'):
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
