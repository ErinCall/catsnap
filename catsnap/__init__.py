from __future__ import unicode_literals
import os
import sys
import getpass
import boto
import ConfigParser

from catsnap import settings

class Config(object):

    CREDENTIALS_FILE = os.path.join(os.environ['HOME'], '.boto')
    CONFIG_FILE = os.path.join(os.environ['HOME'], '.catsnap')
    parser = None

    _instance = None
    _tables = {}

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
        bucket_name = self._bucket_name()
        s3 = boto.connect_s3()
        all_buckets = [x.name for x in s3.get_all_buckets()]
        if bucket_name not in all_buckets:
            bucket = s3.create_bucket(bucket_name)
        else:
            bucket = s3.get_bucket(bucket_name)
        return bucket

    def table(self, table_name):
        table_prefix = self._table_prefix()
        table_name = '%s-%s' % (table_prefix, table_name)

        if table_name in self._tables:
            return self._tables[table_name]
        dynamo = boto.connect_dynamodb()
        all_tables = dynamo.list_tables()
        if table_name not in all_tables:
            schema = dynamo.create_schema(hash_key_name='tag',
                    hash_key_proto_value='S')
            table = dynamo.create_table(name=table_name,
                    schema=schema,
                    read_units=3,
                    write_units=5)
        else:
            table = dynamo.get_table(table_name)
        return table

    def _bucket_name(self):
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
