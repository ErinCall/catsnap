from __future__ import unicode_literals

import boto
import tempfile
from mock import patch, call, Mock
from nose.tools import eq_

from catsnap import settings
from catsnap import botoconf

class TestBotoConf():

    @patch('catsnap.botoconf.sys')
    @patch('catsnap.botoconf.os.path')
    @patch('catsnap.botoconf.get_aws_credentials')
    @patch('catsnap.botoconf.get_catsnap_config')
    def test_ensure_config_files_exist__degenerate_case(self, path,
            setup_boto, setup_catsnap, sys):

        path.exists.return_value = True
        botoconf.ensure_config_files_exist()
        eq_(setup_boto.call_count, 0, "get_aws_credentials shouldn't've "
                "been called")
        eq_(setup_catsnap.call_count, 0, "get_catsnap_config shouldn't've "
                "been called")
        eq_(sys.stdout.write.call_count, 0, "stdout.write shouldn't've "
                "been called")

    #using @patch(os.path) here will F up the mkstemp call :(
    @patch('catsnap.botoconf.sys')
    @patch('catsnap.botoconf.get_catsnap_config')
    @patch('catsnap.botoconf.get_aws_credentials')
    def test_ensure_aws_config_exists(self, get_creds, get_config, sys):
        get_config.side_effect = AssertionError("shouldn't've been called")
        get_creds.return_value = 'the credentials'
        (_, creds) = tempfile.mkstemp()

        with patch('catsnap.botoconf.os.path') as path:
            path.exists.side_effect = [ True, False, True, False ]
            with patch('catsnap.botoconf.CREDENTIALS_FILE', creds) as _:
                botoconf.ensure_config_files_exist()
        with open(creds, 'r') as creds_file:
            eq_(creds_file.read(), 'the credentials')
        sys.stdout.write.assert_called_with(
                "Looks like this is your first run.\n")

    #using @patch(os.path) here will F up the mkstemp call :(
    @patch('catsnap.botoconf.sys')
    @patch('catsnap.botoconf.get_aws_credentials')
    @patch('catsnap.botoconf.get_catsnap_config')
    def test_ensure_catsnap_config_exists(self, get_config, get_creds, sys):
        get_creds.side_effect = AssertionError("shouldn't've been called")
        get_config.return_value = 'the config'
        (_, creds) = tempfile.mkstemp()

        with patch('catsnap.botoconf.os.path') as path:
            path.exists.side_effect = [ False, True, False, True ]
            with patch('catsnap.botoconf.CONFIG_FILE', creds) as _:
                botoconf.ensure_config_files_exist()
        with open(creds, 'r') as creds_file:
            eq_(creds_file.read(), 'the config')
        sys.stdout.write.assert_called_with(
                "Looks like this is your first run.\n")

    @patch('catsnap.botoconf.getpass')
    @patch('catsnap.botoconf.sys')
    def test_get_credentials(self, sys, getpass):
        getpass.getpass.side_effect = ['access key id', 'secret access key']

        creds = botoconf.get_aws_credentials()
        sys.stdout.write.assert_called_with("Find your credentials at "
                "https://portal.aws.amazon.com/gp/aws/securityCredentials\n")
        eq_(creds, """[Credentials]
aws_access_key_id = access key id
aws_secret_access_key = secret access key""")

    @patch('catsnap.botoconf.os')
    @patch('catsnap.botoconf._input')
    def test_get_catsnap_config(self, _input, os):
        os.environ.__getitem__.return_value = 'mcgee'
        _input.return_value = ''

        config = botoconf.get_catsnap_config()
        _input.assert_called_with("Please name your bucket (leave blank to use "
                                  "'catsnap-mcgee'): "),
        eq_(config, """[catsnap]
bucket = catsnap-mcgee""")

class TestConnect():
    @patch('catsnap.botoconf.boto')
    def test_does_not_create_already_existing_bucket(self, mock_boto):
        mock_bucket = Mock()
        mock_bucket.name = settings.BUCKET_BASE
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
        s3.create_bucket.assert_called_with(settings.BUCKET_BASE)
        eq_(bucket, mock_bucket)
