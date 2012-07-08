from __future__ import unicode_literals

import boto
import tempfile
from mock import patch, call, Mock
from nose.tools import eq_

from catsnap import settings
from catsnap import config

class TestConfig():

    @patch('catsnap.config.sys')
    @patch('catsnap.config.get_aws_credentials')
    @patch('catsnap.config.get_catsnap_config')
    def test_ensure_config_files_exist__degenerate_case(self, setup_boto,
            setup_catsnap, sys):
        (_, creds) = tempfile.mkstemp()

        with patch('catsnap.config.os.path') as path:
            path.exists.return_value = True
            with patch('catsnap.config.CREDENTIALS_FILE', creds) as _:
                config.ensure_config_files_exist()
        eq_(setup_boto.call_count, 0, "get_aws_credentials shouldn't've "
                "been called")
        eq_(setup_catsnap.call_count, 0, "get_catsnap_config shouldn't've "
                "been called")
        eq_(sys.stdout.write.call_count, 0, "stdout.write shouldn't've "
                "been called")

    #using @patch(os.path) here will F up the mkstemp call :(
    @patch('catsnap.config.sys')
    @patch('catsnap.config.get_catsnap_config')
    @patch('catsnap.config.get_aws_credentials')
    def test_ensure_aws_config_exists(self, get_creds, get_config, sys):
        get_config.side_effect = AssertionError("shouldn't've been called")
        get_creds.return_value = 'the credentials'
        (_, creds) = tempfile.mkstemp()

        with patch('catsnap.config.os.path') as path:
            path.exists.side_effect = [ True, False, True, False ]
            with patch('catsnap.config.CREDENTIALS_FILE', creds) as _:
                config.ensure_config_files_exist()
        with open(creds, 'r') as creds_file:
            eq_(creds_file.read(), 'the credentials')
        sys.stdout.write.assert_called_with(
                "Looks like this is your first run.\n")

    #using @patch(os.path) here will F up the mkstemp call :(
    @patch('catsnap.config.sys')
    @patch('catsnap.config.get_aws_credentials')
    @patch('catsnap.config.get_catsnap_config')
    def test_ensure_catsnap_config_exists(self, get_config, get_creds, sys):
        get_creds.side_effect = AssertionError("shouldn't've been called")
        get_config.return_value = 'the config'
        (_, conf) = tempfile.mkstemp()

        with patch('catsnap.config.os.path') as path:
            path.exists.side_effect = [ False, True, False, True ]
            with patch('catsnap.config.CONFIG_FILE', conf) as _:
                config.ensure_config_files_exist()
        with open(conf, 'r') as config_file:
            eq_(config_file.read(), 'the config')
        sys.stdout.write.assert_called_with(
                "Looks like this is your first run.\n")

    @patch('catsnap.config.getpass')
    @patch('catsnap.config.sys')
    def test_get_credentials(self, sys, getpass):
        getpass.getpass.side_effect = ['access key id', 'secret access key']

        creds = config.get_aws_credentials()
        sys.stdout.write.assert_called_with("Find your credentials at "
                "https://portal.aws.amazon.com/gp/aws/securityCredentials\n")
        eq_(creds, """[Credentials]
aws_access_key_id = access key id
aws_secret_access_key = secret access key""")

    @patch('catsnap.config.os')
    @patch('catsnap.config._input')
    def test_get_catsnap_config(self, _input, os):
        os.environ.__getitem__.return_value = 'mcgee'
        _input.return_value = ''

        conf = config.get_catsnap_config()
        _input.assert_called_with("Please name your bucket (leave blank to use "
                                  "'catsnap-mcgee'): "),
        eq_(conf, """[catsnap]
bucket = catsnap-mcgee""")

class TestConnect():
    @patch('catsnap.config._bucket_name')
    @patch('catsnap.config.boto')
    def test_does_not_re_create_buckets(self, mock_boto, _bucket_name):
        _bucket_name.return_value = 'oodles'
        mock_bucket = Mock()
        mock_bucket.name = 'oodles'
        s3 = Mock()
        s3.get_all_buckets.return_value = [ mock_bucket ]
        s3.get_bucket.return_value = mock_bucket
        mock_boto.connect_s3.return_value = s3

        bucket = config.connect()
        eq_(s3.create_bucket.call_count, 0, "shouldn't've created a bucket")
        eq_(bucket, mock_bucket)

    @patch('catsnap.config._bucket_name')
    @patch('catsnap.config.boto')
    def test_creates_bucket_if_necessary(self, mock_boto, _bucket_name):
        _bucket_name.return_value = 'galvanized'
        s3 = Mock()
        mock_bucket = Mock()
        s3.create_bucket.return_value = mock_bucket
        s3.get_all_buckets.return_value = []
        mock_boto.connect_s3.return_value = s3

        bucket = config.connect()
        s3.create_bucket.assert_called_with('galvanized')
        eq_(bucket, mock_bucket)

    def test_determine_bucket_name(self):
        (_, conf) = tempfile.mkstemp()
        with open(conf, 'w') as config_file:
            config_file.write("""[catsnap]
bucket = boogles""")

        with patch('catsnap.config.CONFIG_FILE', conf) as _:
            bucket_name = config._bucket_name()
        eq_(bucket_name, 'boogles')
