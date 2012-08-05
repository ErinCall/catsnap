from __future__ import unicode_literals

from mock import patch, call, Mock
from nose.tools import eq_, ok_
from tests import TestCase
from ConfigParser import ConfigParser

from catsnap.config.file_config import FileConfig

class FileConfigTester(TestCase):
    def _set_parser_defaults(self, parser):
        parser.add_section('Credentials')
        parser.add_section('catsnap')
        parser.set('Credentials', 'aws_access_key_id', 'itsme')
        parser.set('Credentials', 'aws_secret_access_key', 'letmein')
        parser.set('catsnap', 'bucket', 'mypics')

class TestFileConfig(FileConfigTester):
    def test_getitem(self):
        config = FileConfig()
        self._set_parser_defaults(config._parser)

        eq_(config['bucket'], 'mypics')
        eq_(config['aws_access_key_id'], 'itsme')
        eq_(config['aws_secret_access_key'], 'letmein')

    def test_contains(self):
        config = FileConfig()
        self._set_parser_defaults(config._parser)
        ok_('bucket' in config)
        ok_('aws_access_key_id' in config)
        ok_('mellifluous' not in config)

    def test_contains__false_if_files_empty(self):
        config = FileConfig()
        ok_('bucket' not in config)

    def test_reads_config_file(self):
        with open(self.config_tempfile, 'w') as config:
            config.write("""[catsnap]
bucket = boogles
[Credentials]
aws_access_key_id = itsme""")

        config = FileConfig()
        ok_(config._parser.has_option('Credentials', 'aws_access_key_id'))
        ok_(config._parser.has_option('catsnap', 'bucket'))

    def test_reads_legacy_boto_file(self):
        with open(self.creds_tempfile, 'w') as credentials:
            credentials.write("""[Credentials]
aws_access_key_id = itsme""")

        config = FileConfig()
        ok_(config._parser.has_option('Credentials', 'aws_access_key_id'))

    def test_config_file_overrules_legacy_boto_file(self):
        with open(self.creds_tempfile, 'w') as credentials:
            credentials.write("""[Credentials]
aws_access_key_id = itsme""")
        with open(self.config_tempfile, 'w') as config:
            config.write("""[Credentials]
aws_access_key_id = hereiam""")

        config = FileConfig()
        eq_(config._parser.get('Credentials', 'aws_access_key_id'), 'hereiam')

class TestCollectSettings(FileConfigTester):
    @patch('catsnap.config.file_config.FileConfig._input')
    @patch('catsnap.config.file_config.getpass')
    @patch('catsnap.config.file_config.sys')
    def test_get_credentials(self, sys, getpass, _input):
        getpass.getpass.return_value = 'secret access key'
        _input.return_value = 'access key id'

        config = FileConfig()
        config.collect_settings()
        sys.stdout.write.assert_called_with("Find your credentials at "
                "https://portal.aws.amazon.com/gp/aws/securityCredentials\n")
        eq_(config._parser.get('Credentials', 'aws_access_key_id'),
                'access key id')
        eq_(config._parser.get('Credentials', 'aws_secret_access_key'),
                'secret access key')

    @patch('catsnap.config.file_config.os')
    @patch('catsnap.config.file_config.FileConfig._input')
    def test_get_catsnap_config(self, _input, os):
        os.environ.__getitem__.return_value = 'mcgee'
        _input.return_value = ''

        config = FileConfig()
        config.collect_settings()
        _input.assert_has_calls([
            call('Enter your access key id: '),
            call("Please name your bucket (leave "
                "blank to use 'catsnap-mcgee'): ")])
        eq_(config._parser.get('catsnap', 'bucket'), 'catsnap-mcgee')

    @patch('catsnap.config.file_config.os')
    @patch('catsnap.config.file_config.FileConfig._input')
    def test_set_custom_bucket_name(self, _input, os):
        os.environ.__getitem__.return_value = 'mcgee'
        _input.side_effect = [
                '', # key id
                'booya'] # bucket

        config = FileConfig()
        config.collect_settings(settings_to_get=[])
        eq_(config._parser.get('catsnap', 'bucket'), 'booya')

    @patch('catsnap.config.file_config.os')
    @patch('catsnap.config.file_config.getpass')
    @patch('catsnap.config.file_config.FileConfig._input')
    def test_change_config(self, _input, getpass, os):
        os.environ.__getitem__.return_value = 'mcgee'
        config = FileConfig()
        self._set_parser_defaults(config._parser)

        _input.side_effect = [ 'hereiam', 'catsnap-giggity' ]
        getpass.getpass.return_value = 'pa55word'

        config.collect_settings()
        _input.assert_has_calls([
                call("Enter your access key id (leave blank to keep using "
                        "'itsme'): "),
                call("Please name your bucket (leave blank to use "
                        "'mypics'): ")])
        getpass.getpass.assert_called_once_with('Enter your secret access key '
                '(leave blank to keep using what you had before): ')
        eq_(config._parser.get('Credentials', 'aws_access_key_id'), 'hereiam')
        eq_(config._parser.get('Credentials', 'aws_secret_access_key'), 'pa55word')
        eq_(config._parser.get('catsnap', 'bucket'), 'catsnap-giggity')
        with open(self.config_tempfile, 'r') as config_file:
            eq_(config_file.read(), """[Credentials]
aws_access_key_id = hereiam
aws_secret_access_key = pa55word

[catsnap]
bucket = catsnap-giggity

""")

    @patch('catsnap.config.file_config.os')
    @patch('catsnap.config.file_config.getpass')
    @patch('catsnap.config.file_config.FileConfig._input')
    def test_entering_nothing_changes_nothing(self, _input, getpass, os):
        os.environ.__getitem__.return_value = 'mcgee'
        config = FileConfig()
        self._set_parser_defaults(config._parser)

        _input.return_value = ''
        getpass.getpass.return_value = ''

        config.collect_settings()
        eq_(config._parser.get('Credentials', 'aws_access_key_id'), 'itsme')
        eq_(config._parser.get('Credentials', 'aws_secret_access_key'), 'letmein')
        eq_(config._parser.get('catsnap', 'bucket'), 'mypics')

    @patch('catsnap.config.file_config.FileConfig._input')
    def test_set_only_one_setting_name(self, _input):
        config = FileConfig()
        self._set_parser_defaults(config._parser)
        _input.return_value = 'truckit'

        config.collect_settings(settings_to_get='bucket')
        _input.assert_called_once_with("Please name your bucket (leave blank "
                "to use 'mypics'): ")
        eq_(config._parser.get('catsnap', 'bucket'), 'truckit')

