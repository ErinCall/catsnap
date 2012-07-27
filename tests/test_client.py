from __future__ import unicode_literals

from tests import TestCase
import boto
from mock import patch, call, Mock
from nose.tools import eq_

from catsnap import Client

class TestSetup(TestCase):
    @patch('catsnap.Client.create_table')
    def test_creates_tables(self, create_table):
        client = Client()
        tables_created = client.setup()
        create_table.assert_has_calls([
            call('tag'),
            call('image')])
        eq_(tables_created, 2)

    @patch('catsnap.Client.create_table')
    def test_returns_number_of_new_tables(self, create_table):
        error = boto.exception.DynamoDBResponseError(400, 'table exists')
        error.error_code = 'ResourceInUseException'
        def do_create_table(table_name):
            if table_name == 'tag':
                return Mock()
            else:
                raise error
        create_table.side_effect = do_create_table

        client = Client()
        tables_created = client.setup()

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

        bucket = Client().bucket()
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

        bucket = Client().bucket()
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

        bucket1 = Client().bucket()
        bucket2 = Client().bucket()
        assert bucket1 is bucket2, 'multiple s3 connections were established'
        eq_(s3.get_bucket.call_count, 1)

class TestGetTable(TestCase):
    @patch('catsnap.Config._table_prefix')
    def test_memoization(self, _table_prefix):
        _table_prefix.return_value = 'foo'
        client = Client()
        mock_table = Mock()
        client._dynamo_connection = Mock()
        client._dynamo_connection.get_table.return_value = mock_table

        table = client.table('tags')
        eq_(table, mock_table)
        eq_(client._dynamo_connection.get_table.call_count, 1)
        table = client.table('tags')
        eq_(client._dynamo_connection.get_table.call_count, 1)

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

        table = Client().create_table('things')
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
        Client().get_dynamodb()
        eq_(boto.connect_dynamodb.call_count, 1)

    @patch('catsnap.boto')
    def test_get_dynamodb__is_memoized(self, boto):
        boto.connect_dynamodb.side_effect = [1, 2]
        dynamo1 = Client().get_dynamodb()
        dynamo2 = Client().get_dynamodb()

        assert dynamo1 is dynamo2, 'different connections were established'
        eq_(boto.connect_dynamodb.call_count, 1)

    @patch('catsnap.Config._access_key_id')
    @patch('catsnap.Config._secret_access_key')
    @patch('catsnap.boto')
    def test_get_s3(self, boto, _secret_access_key, _access_key_id):
        _secret_access_key.return_value = 'letmein'
        _access_key_id.return_value = 'itsme'
        Client().get_s3()
        boto.connect_s3.assert_called_once_with(
                aws_secret_access_key='letmein', aws_access_key_id='itsme')

    @patch('catsnap.boto')
    def test_get_s3__is_memoized(self, boto):
        boto.connect_dynamodb.side_effect = [1, 2]
        sss1 = Client().get_s3()
        sss2 = Client().get_s3()

        assert sss1 is sss2, 'different connections were established'
        eq_(boto.connect_s3.call_count, 1)

