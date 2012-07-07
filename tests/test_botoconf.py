from __future__ import print_function, unicode_literals

import tempfile
from mock import patch
from nose.tools import eq_

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
        sys.stdout.write.assert_called_with("Looks like this is your first run.\n")
        eq_(creds, """[Credentials]
aws_access_key_id = access key id
aws_secret_access_key = secret access key""")
