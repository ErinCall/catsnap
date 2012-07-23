from __future__ import unicode_literals

import boto
import tempfile
from mock import patch, call, Mock
from nose.tools import eq_
from tests import TestCase

from catsnap import settings
from catsnap import Config, HASH_KEY

class TestConfig(TestCase):
    def test_it_is_a_singleton(self):
        config1 = Config()
        config2 = Config()
        assert config1 is config2

    @patch('catsnap.Config._input')
    @patch('catsnap.getpass')
    @patch('catsnap.sys')
    def test_get_credentials(self, sys, getpass, _input):
        getpass.getpass.return_value = 'secret access key'
        _input.return_value = 'access key id'

        config = Config()
        sys.stdout.write.assert_called_with("Find your credentials at "
                "https://portal.aws.amazon.com/gp/aws/securityCredentials\n")
        eq_(config.parser.get('Credentials', 'aws_access_key_id'),
                'access key id')
        eq_(config.parser.get('Credentials', 'aws_secret_access_key'),
                'secret access key')

    @patch('catsnap.Config.get_credentials')
    @patch('catsnap.os')
    @patch('catsnap.Config._input')
    def test_get_catsnap_config(self, _input, os, get_credentials):
        os.environ.__getitem__.return_value = 'mcgee'
        _input.return_value = ''

        config = Config()
        _input.assert_called_once_with("Please name your bucket (leave "
                "blank to use 'catsnap-mcgee'): ")
        eq_(config.parser.get('catsnap', 'bucket'), 'catsnap-mcgee')
        eq_(config.parser.get('catsnap', 'table_prefix'), 'catsnap-mcgee')

    @patch('catsnap.os')
    @patch('catsnap.Config._input')
    @patch('catsnap.Config.get_credentials')
    def test_get_catsnap_config__one_custom_name(self, get_credentials,
                                                 _input, os):
        os.environ.__getitem__.return_value = 'mcgee'
        _input.side_effect = ['booya', '']

        config = Config()
        eq_(config.parser.get('catsnap', 'bucket'), 'booya')
        eq_(config.parser.get('catsnap', 'table_prefix'), 'booya')

    @patch('catsnap.Config.get_credentials')
    @patch('catsnap.Config.get_config')
    def test_create_config_withut_setting_up(self, get_config,
            get_credentials):
        config = Config(get_missing_settings=False)
        assert not get_credentials.called
        assert not get_config.called

    @patch('catsnap.os')
    @patch('catsnap.getpass')
    @patch('catsnap.Config._input')
    def test_change_config(self, _input, getpass, os):
        os.environ.__getitem__.return_value = 'mcgee'
        config = Config(get_missing_settings=False)
        config.parser.add_section('Credentials')
        config.parser.add_section('catsnap')
        config.parser.set('Credentials', 'aws_access_key_id', 'itsme')
        config.parser.set('Credentials', 'aws_secret_access_key', 'letmein')
        config.parser.set('catsnap', 'bucket', 'mypics')
        config.parser.set('catsnap', 'table_prefix', 'mypics')

        _input.side_effect = [ 'hereiam', 'catsnap-giggity' ]
        getpass.getpass.return_value = 'pa55word'

        config.get_settings(override_existing=True)
        _input.assert_has_calls([
                call("Enter your access key id (leave blank to keep using "
                        "'itsme'): "),
                call("Please name your bucket (leave blank to keep using "
                        "'mypics'): ")])
        getpass.getpass.assert_called_once_with('Enter your secret access key '
                '(leave blank to keep using what you had before): ')
        eq_(config.parser.get('Credentials', 'aws_access_key_id'), 'hereiam')
        eq_(config.parser.get('Credentials', 'aws_secret_access_key'), 'pa55word')
        eq_(config.parser.get('catsnap', 'bucket'), 'catsnap-giggity')
        eq_(config.parser.get('catsnap', 'table_prefix'), 'catsnap-giggity')

    @patch('catsnap.os')
    @patch('catsnap.getpass')
    @patch('catsnap.Config._input')
    def test_change_config(self, _input, getpass, os):
        os.environ.__getitem__.return_value = 'mcgee'
        config = Config(get_missing_settings=False)
        config.parser.add_section('Credentials')
        config.parser.add_section('catsnap')
        config.parser.set('Credentials', 'aws_access_key_id', 'itsme')
        config.parser.set('Credentials', 'aws_secret_access_key', 'letmein')
        config.parser.set('catsnap', 'bucket', 'mypics')
        config.parser.set('catsnap', 'table_prefix', 'mypics')

        _input.return_value = ''
        getpass.getpass.return_value = ''

        config.get_settings(override_existing=True)
        eq_(config.parser.get('Credentials', 'aws_access_key_id'), 'itsme')
        eq_(config.parser.get('Credentials', 'aws_secret_access_key'), 'letmein')
        eq_(config.parser.get('catsnap', 'bucket'), 'mypics')
        eq_(config.parser.get('catsnap', 'table_prefix'), 'mypics')

    @patch('catsnap.Config._input')
    def test_change_config__does_not_override_custom_table_prefix(self, _input):
        existing_settings = {
                'bucket': 'im-ah-gezz',
                'table_prefix': 'that-catsnap-thing'}
        def get_setting(section, setting_name):
            if section != 'catsnap':
                raise ValueError(section)
            return existing_settings[setting_name]
        config = Config(get_missing_settings=False)
        config.parser = Mock()
        config.parser.get.side_effect = get_setting
        config.parser.has_option.return_value = True
        _input.return_value = 'pics'

        config.get_config(override_existing=True)
        config.parser.set.assert_called_once_with('catsnap', 'bucket', 'pics')

class TestSetup(TestCase):
    @patch('catsnap.Config.create_table')
    def test_creates_tables(self, create_table):
        config = Config()
        tables_created = config.setup()
        create_table.assert_has_calls([
            call('tag'),
            call('image')])
        eq_(tables_created, 2)

    @patch('catsnap.Config.create_table')
    def test_returns_number_of_new_tables(self, create_table):
        error = boto.exception.DynamoDBResponseError(400, 'table exists')
        error.error_code = 'ResourceInUseException'
        def do_create_table(table_name):
            if table_name == 'tag':
                return Mock()
            else:
                raise error
        create_table.side_effect = do_create_table

        config = Config()
        tables_created = config.setup()

        eq_(tables_created, 1)

class TestGetBucket(TestCase):
    @patch('catsnap.Config.bucket_name')
    @patch('catsnap.boto')
    def test_does_not_re_create_buckets(self, mock_boto, bucket_name):
        bucket_name.return_value = 'oodles'
        mock_bucket = Mock()
        mock_bucket.name = 'oodles'
        s3 = Mock()
        s3.get_all_buckets.return_value = [ mock_bucket ]
        s3.get_bucket.return_value = mock_bucket
        mock_boto.connect_s3.return_value = s3

        bucket = Config().bucket()
        eq_(s3.create_bucket.call_count, 0, "shouldn't've created a bucket")
        eq_(bucket, mock_bucket)

    @patch('catsnap.Config.bucket_name')
    @patch('catsnap.boto')
    def test_creates_bucket_if_necessary(self, mock_boto, bucket_name):
        bucket_name.return_value = 'galvanized'
        s3 = Mock()
        mock_bucket = Mock()
        s3.create_bucket.return_value = mock_bucket
        s3.get_all_buckets.return_value = []
        mock_boto.connect_s3.return_value = s3

        bucket = Config().bucket()
        s3.create_bucket.assert_called_with('galvanized')
        eq_(bucket, mock_bucket)

    @patch('catsnap.Config.bucket_name')
    @patch('catsnap.boto')
    def test_get_bucket_is_memoized(self, mock_boto, bucket_name):
        bucket_name.return_value = 'oodles'
        mock_bucket = Mock()
        mock_bucket.name = 'oodles'
        s3 = Mock()
        s3.get_all_buckets.return_value = [ mock_bucket ]
        s3.get_bucket.side_effect = [ 1, 2 ]
        mock_boto.connect_s3.return_value = s3

        bucket1 = Config().bucket()
        bucket2 = Config().bucket()
        assert bucket1 is bucket2, 'multiple s3 connections were established'
        eq_(s3.get_bucket.call_count, 1)

class TestGetTable(TestCase):
    @patch('catsnap.Config._table_prefix')
    def test_memoization(self, _table_prefix):
        _table_prefix.return_value = 'foo'
        config = Config()
        mock_table = Mock()
        config._dynamo_connection = Mock()
        config._dynamo_connection.get_table.return_value = mock_table

        table = config.table('tags')
        eq_(table, mock_table)
        eq_(config._dynamo_connection.get_table.call_count, 1)
        table = config.table('tags')
        eq_(config._dynamo_connection.get_table.call_count, 1)

class TestCreateTable(TestCase):
    @patch('catsnap.Config._table_prefix')
    @patch('catsnap.boto')
    def test_create_table(self, mock_boto, _table_prefix):
        _table_prefix.return_value = 'myemmatable'
        dynamo = Mock()
        mock_table = Mock()
        schema = Mock()
        dynamo.create_table.return_value = mock_table
        dynamo.create_schema.return_value = schema
        mock_boto.connect_dynamodb.return_value = dynamo

        table = Config().create_table('things')
        dynamo.create_schema.assert_called_with(
                hash_key_name='tag',
                hash_key_proto_value='S')
        dynamo.create_table.assert_called_with(name='myemmatable-things',
                schema=schema,
                read_units=3,
                write_units=5)
        eq_(table, mock_table)

class TestGetConnections(TestCase):
    @patch('catsnap.boto')
    def test_get_dynamodb(self, boto):
        Config().get_dynamodb()
        eq_(boto.connect_dynamodb.call_count, 1)

    @patch('catsnap.boto')
    def test_get_dynamodb__is_memoized(self, boto):
        boto.connect_dynamodb.side_effect = [1, 2]
        dynamo1 = Config().get_dynamodb()
        dynamo2 = Config().get_dynamodb()

        assert dynamo1 is dynamo2, 'different connections were established'
        eq_(boto.connect_dynamodb.call_count, 1)

    @patch('catsnap.Config._access_key_id')
    @patch('catsnap.Config._secret_access_key')
    @patch('catsnap.boto')
    def test_get_s3(self, boto, _secret_access_key, _access_key_id):
        _secret_access_key.return_value = 'letmein'
        _access_key_id.return_value = 'itsme'
        Config().get_s3()
        boto.connect_s3.assert_called_once_with(
                aws_secret_access_key='letmein', aws_access_key_id='itsme')

    @patch('catsnap.boto')
    def test_get_s3__is_memoized(self, boto):
        boto.connect_dynamodb.side_effect = [1, 2]
        sss1 = Config().get_s3()
        sss2 = Config().get_s3()

        assert sss1 is sss2, 'different connections were established'
        eq_(boto.connect_s3.call_count, 1)
