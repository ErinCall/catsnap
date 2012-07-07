from __future__ import unicode_literals

import boto
import tempfile
from mock import patch, call, Mock
from nose.tools import eq_

from catsnap import settings
from catsnap import botoconf

class TestBotoConf():
    @patch('catsnap.botoconf.os.path')
    @patch('catsnap.botoconf.get_aws_credentials')
    def test_does_nothing_if_aws_cred_file_exists(self, path, get_creds):
        path.exists.return_value = True
        botoconf.ensure_aws_credentials_exist()
        eq_(get_creds.call_count, 0, "get_creds shouldn't've been called")

    @patch('catsnap.botoconf.get_aws_credentials')
    def test_writes_contents_to_file(self, get_creds):
        get_creds.return_value = 'the credentials'
        (_, creds) = tempfile.mkstemp()
        with patch('catsnap.botoconf.os.path') as path:
            path.exists.return_value = False
            with patch('catsnap.botoconf.CREDENTIALS_FILE', creds) as _:
                botoconf.ensure_aws_credentials_exist()
        with open(creds, 'r') as creds_file:
            eq_(creds_file.read(), 'the credentials')

    @patch('catsnap.botoconf.getpass')
    @patch('catsnap.botoconf.sys')
    def test_get_credentials(self, sys, getpass):
        getpass.getpass.side_effect = ['access key id', 'secret access key']
        creds = botoconf.get_aws_credentials()
        sys.stdout.write.assert_has_calls([
            call("Looks like this is your first run.\n"),
            call("Find your credentials at https://portal.aws.amazon.com/gp/"
                 "aws/securityCredentials\n"),])
        eq_(creds, """[Credentials]
aws_access_key_id = access key id
aws_secret_access_key = secret access key""")

class TestConnect():
    @patch('catsnap.botoconf.boto')
    def test_does_not_create_already_existing_bucket(self, mock_boto):
        mock_bucket = Mock()
        mock_bucket.name = settings.BUCKET
        s3 = Mock()
        s3.get_all_buckets.return_value = [ mock_bucket ]
        s3.get_bucket.return_value = mock_bucket
        mock_boto.connect_s3.return_value = s3

        bucket = botoconf.connect()
        eq_(s3.create_bucket.call_count, 0, "shouldn't've created a bucket")
        eq_(bucket, mock_bucket)

    @patch('catsnap.botoconf.boto')
    def test_creates_bucket_if_necessary(self, mock_boto):
        s3 = Mock()
        mock_bucket = Mock()
        s3.create_bucket.return_value = mock_bucket
        s3.get_all_buckets.return_value = []
        mock_boto.connect_s3.return_value = s3

        bucket = botoconf.connect()
        s3.create_bucket.assert_called_with(settings.BUCKET)
        eq_(bucket, mock_bucket)
