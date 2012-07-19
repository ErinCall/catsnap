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
            cls._instance = super(Config, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        self.ensure_config_files_exist()

    def ensure_config_files_exist(self):
        if not all(map(os.path.exists, [ self.CONFIG_FILE,
                                         self.CREDENTIALS_FILE ])):
            sys.stdout.write("Looks like this is your first run.\n")
            if not os.path.exists(self.CONFIG_FILE):
                config = self.get_catsnap_config()
                with open(self.CONFIG_FILE, 'w', 0600) as config_file:
                    config_file.write(config)
            if not os.path.exists(self.CREDENTIALS_FILE):
                credentials = self.get_aws_credentials()
                with open(self.CREDENTIALS_FILE, 'w', 0600) as creds_file:
                    creds_file.write(credentials)
        else:
            return

    def get_aws_credentials(self):
        sys.stdout.write("Find your credentials at https://portal.aws.amazon.com/"
                         "gp/aws/securityCredentials\n")
        key_id = getpass.getpass('Enter your access key id: ')
        key = getpass.getpass('Enter your secret access key: ')
        return """[Credentials]
aws_access_key_id = %(key_id)s
aws_secret_access_key = %(key)s""" % {'key_id': key_id, 'key': key}

    def get_catsnap_config(self):
        bucket_name = '%s-%s' % (settings.BUCKET_BASE, os.environ['USER'])
        actual_bucket_name = self._input("Please name your bucket (leave blank to "
                "use '%s'): " % bucket_name)
        bucket_name = actual_bucket_name or bucket_name

        table_prefix = bucket_name
        actual_table_prefix = self._input("Please choose a table prefix "
                "(leave blank to use '%s'): " % table_prefix)
        table_prefix = actual_table_prefix or table_prefix
        return """[catsnap]
bucket = %s
table_prefix = %s""" % (bucket_name, table_prefix)

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
        try:
            table = dynamo.create_table(name=table_name,
                    schema=schema,
                    read_units=3,
                    write_units=5)
        except DynamoDBResponseError, e:
            if e.error_code == 'ResourceInUseException':
                return self.table(table_name)
            else:
                raise
        return table

    def table(self, table_name):
        table_prefix = self._table_prefix()
        table_name = '%s-%s' % (table_prefix, table_name)

        if table_name in self._tables:
            return self._tables[table_name]
        dynamo = self.get_dynamodb()
        return dynamo.get_table(table_name)

    def get_dynamodb(self):
        if not self._dynamo_connection:
            self._dynamo_connection = boto.connect_dynamodb()
        return self._dynamo_connection

    def get_s3(self):
        if not self._s3_connection:
            self._s3_connection = boto.connect_s3()
        return self._s3_connection

    def bucket_name(self):
        return self._parser().get('catsnap', 'bucket')

    def _table_prefix(self):
        return self._parser().get('catsnap', 'table_prefix')

    def _parser(self):
        if self.parser is None:
            parser = ConfigParser.ConfigParser()
            parser.read(self.CONFIG_FILE)
            self.parser = parser
        return self.parser

    def _input(self, *args, **kwargs):
        return raw_input(*args, **kwargs)
