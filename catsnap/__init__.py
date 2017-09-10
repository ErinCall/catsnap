import boto
import os

from catsnap.config import Config
from catsnap.singleton import Singleton
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from threading import Lock

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
    _cloudfront_connection = None
    _cloudfront_url = None
    _engine = None
    _session = None

    def config(self, new_config=None):
        if new_config is not None:
            self._config = new_config
        if self._config is None:
            self._config = Config()
        return self._config

    def bucket(self):
        if not self._bucket:
            s3 = self.get_s3()
            bucket_name = self.config()['aws.bucket']
            self._bucket = s3.get_bucket(bucket_name)
        return self._bucket

    def table(self, table_name):
        table_prefix = self.config()['aws.bucket']
        table_name = '%s-%s' % (table_prefix, table_name)

        if table_name not in self._tables:
            dynamo = self.get_dynamodb()
            self._tables[table_name] = dynamo.get_table(table_name)
        return self._tables[table_name]

    def get_dynamodb(self):
        if not self._dynamo_connection:
            self._dynamo_connection = boto.connect_dynamodb(
                    aws_access_key_id=self.config()['aws.access_key_id'],
                    aws_secret_access_key=self.config()['aws.secret_access_key'])
        return self._dynamo_connection

    def get_s3(self):
        if not self._s3_connection:
            self._s3_connection = boto.connect_s3(
                    aws_access_key_id=self.config()['aws.access_key_id'],
                    aws_secret_access_key=self.config()['aws.secret_access_key'])
        return self._s3_connection

    def get_cloudfront(self):
        if not self._cloudfront_connection:
            self._cloudfront_connection = boto.connect_cloudfront(
                    aws_access_key_id=self.config()['aws.access_key_id'],
                    aws_secret_access_key=self.config()['aws.secret_access_key'])
        return self._cloudfront_connection

    def session(self):
        if not self._engine:
            self._engine = create_engine(self.config()['postgres_url'])
        if not self._session:
            self._session = MutexSession(self._engine)
        return self._session

    def cloudfront_url(self, distro_id):
        if self._cloudfront_url is None:
            distro_info = self.get_cloudfront().get_distribution_info(distro_id)
            if len(distro_info.config.cnames) > 0:
                self._cloudfront_url = distro_info.config.cnames[0]
            else:
                self._cloudfront_url = distro_info.domain_name
        return self._cloudfront_url

# "Whoa," you might be thinking, "a thread-safe session manager? Why, when
# Catsnap is single-threaded, as far as I can see?" Well, it's because the
# acceptance tests spin up a second thread while the main thread pokes it
# with a browser.
mutex = Lock()
class MutexSession(object):
    def __init__(self, engine):
        self._session = sessionmaker(bind=engine)()

        def define_function(function_name):
            def function(*args, **kwargs):
                mutex.acquire()
                try:
                    return getattr(self._session, function_name)(*args, **kwargs)
                finally:
                    mutex.release()
            return function

        for function_name in [
                'add',
                'flush',
                'commit',
                'rollback',
                'query',
                'execute',
                'refresh',
                'delete']:
            function = define_function(function_name)
            setattr(self, function_name, function)
