from __future__ import unicode_literals

from tests import TestCase
import boto
from mock import patch, call, Mock
from nose.tools import eq_, assert_raises

from catsnap import Client

class TestGetBucket(TestCase):
    @patch('catsnap.MetaConfig')
    @patch('catsnap.boto')
    def test_does_not_create_buckets(self, mock_boto, MockMetaConfig):
        config = Mock(bucket='oodles', aws_access_key_id='foo',
                aws_secret_access_key='bar')
        MockMetaConfig.return_value = config
        s3 = Mock()
        s3.get_all_buckets.return_value = []
        mock_boto.connect_s3.return_value = s3

        bucket = Client().bucket()
        eq_(s3.create_bucket.call_count, 0, "shouldn't've created a bucket")

    @patch('catsnap.MetaConfig')
    @patch('catsnap.boto')
    def test_get_bucket_is_memoized(self, mock_boto, MockMetaConfig):
        config = Mock(bucket='oodles', aws_access_key_id='foo',
                aws_secret_access_key='bar')
        MockMetaConfig.return_value = config
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
    @patch('catsnap.MetaConfig')
    def test_memoization(self, MockMetaConfig):
        config = Mock(bucket='foo')
        MockMetaConfig.return_value = config
        client = Client()
        mock_table = Mock()
        client._dynamo_connection = Mock()
        client._dynamo_connection.get_table.return_value = mock_table

        table = client.table('tags')
        eq_(table, mock_table)
        eq_(client._dynamo_connection.get_table.call_count, 1)
        table = client.table('tags')
        eq_(client._dynamo_connection.get_table.call_count, 1)

class TestGetConnections(TestCase):
    @patch('catsnap.MetaConfig')
    @patch('catsnap.boto')
    def test_get_dynamodb(self, boto, MockMetaConfig):
        config = Mock(bucket='oodles', aws_access_key_id='foo',
                aws_secret_access_key='bar')
        MockMetaConfig.return_value = config
        Client().get_dynamodb()
        eq_(boto.connect_dynamodb.call_count, 1)

    @patch('catsnap.MetaConfig')
    @patch('catsnap.boto')
    def test_get_dynamodb__is_memoized(self, boto, MockMetaConfig):
        config = Mock(bucket='oodles', aws_access_key_id='foo',
                aws_secret_access_key='bar')
        MockMetaConfig.return_value = config
        boto.connect_dynamodb.side_effect = [1, 2]
        dynamo1 = Client().get_dynamodb()
        dynamo2 = Client().get_dynamodb()

        assert dynamo1 is dynamo2, 'different connections were established'
        eq_(boto.connect_dynamodb.call_count, 1)

    @patch('catsnap.MetaConfig')
    @patch('catsnap.boto')
    def test_get_s3(self, boto, MockMetaConfig):
        config = Mock(aws_access_key_id='itsme', aws_secret_access_key='letmein')
        MockMetaConfig.return_value = config
        Client().get_s3()
        boto.connect_s3.assert_called_once_with(
                aws_secret_access_key='letmein', aws_access_key_id='itsme')


    @patch('catsnap.MetaConfig')
    @patch('catsnap.boto')
    def test_get_s3__is_memoized(self, boto, MockMetaConfig):
        config = Mock(aws_access_key_id='itsme', aws_secret_access_key='letmein')
        MockMetaConfig.return_value = config
        boto.connect_dynamodb.side_effect = [1, 2]
        sss1 = Client().get_s3()
        sss2 = Client().get_s3()

        assert sss1 is sss2, 'different connections were established'
        eq_(boto.connect_s3.call_count, 1)

    def test_connect_to_postgres(self):
        session = Client().session()
        session2 = Client().session()
        assert session is session2, 'multiple engines were created'
        eq_(session.execute('select 1').fetchall(), [(1, )])

