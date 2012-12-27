from __future__ import unicode_literals
import boto
import os

from catsnap.config import MetaConfig
from catsnap.config.file_config import FileConfig
from catsnap.config.env_config import EnvConfig
from catsnap.singleton import Singleton
from boto.exception import DynamoDBResponseError, S3CreateError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

#This really oughtta be, like, the tablename or something, but I screwed up, so
#now there're existing catsnap installs that use this schema. Sucks :(
#So yeah every table is keyed on an attribute called 'tag'
HASH_KEY = 'tag'

class Client(Singleton):
    _tables = {}
    _bucket = None
    _config = None

    _dynamo_connection = None
    _s3_connection = None
    _engine = None
    _session = None

    def config(self, new_config=None):
        if new_config is not None:
            self._config = new_config
        if self._config is None:
            self._config = MetaConfig(FileConfig, EnvConfig)
        return self._config

    def bucket(self):
        if not self._bucket:
            s3 = self.get_s3()
            bucket_name = self.config().bucket
            self._bucket = s3.get_bucket(bucket_name)
        return self._bucket

    def table(self, table_name):
        table_prefix = self.config().bucket
        table_name = '%s-%s' % (table_prefix, table_name)

        if table_name not in self._tables:
            dynamo = self.get_dynamodb()
            self._tables[table_name] = dynamo.get_table(table_name)
        return self._tables[table_name]

    def get_dynamodb(self):
        if not self._dynamo_connection:
            self._dynamo_connection = boto.connect_dynamodb(
                    aws_access_key_id=self.config().aws_access_key_id,
                    aws_secret_access_key=self.config().aws_secret_access_key)
        return self._dynamo_connection

    def get_s3(self):
        if not self._s3_connection:
            self._s3_connection = boto.connect_s3(
                    aws_access_key_id=self.config().aws_access_key_id,
                    aws_secret_access_key=self.config().aws_secret_access_key)
        return self._s3_connection

    def session(self):
        if not self._engine:
            self._engine = create_engine(os.environ['DATABASE_URL'])
        if not self._session:
            self._session = sessionmaker(bind=self._engine)()
        return self._session

