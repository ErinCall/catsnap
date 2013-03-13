from __future__ import unicode_literals

from mock import patch, call, Mock
from nose.tools import eq_, ok_, assert_raises
from tests import TestCase
from ConfigParser import ConfigParser

from catsnap.config.file_config import FileConfig, FileSetting

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

    def test_fails_if_it_does_not_know_about_a_setting_in_all_settings(self):
        with patch('catsnap.config.base.Config.ALL_SETTINGS', ['turbidity']):
            assert_raises(AttributeError, FileConfig)

    def test_get_a_boolean_setting(self):
        with open(self.config_tempfile, 'w') as config:
            config.write("""[catsnap]
extension = no
""")
        config = FileConfig()
        eq_(config['extension'], False)

class TestCollectSettings(FileConfigTester):
    @patch('catsnap.config.file_config._input')
    @patch('catsnap.config.file_config.getpass')
    def test_get_credentials(self, getpass, _input):
        getpass.getpass.return_value = 'secret access key'
        _input.return_value = 'access key id'

        config = FileConfig()
        config.collect_settings()
        eq_(config._parser.get('catsnap', 'api_host'),
                'access key id')
        eq_(config._parser.get('catsnap', 'api_key'),
                'secret access key')

    @patch('catsnap.config.file_config.os')
    @patch('catsnap.config.file_config._input')
    def test_get_catsnap_config(self, _input, os):
        os.environ.get.return_value = 'mcgee'
        _input.return_value = ''

        config = FileConfig()
        config.collect_settings()
        _input.assert_has_calls([
            call("Would you like to print a fake file extension on urls? ")])
        eq_(config._parser.get('catsnap', 'extension'), None)

    @patch('catsnap.config.file_config.os')
    @patch('catsnap.config.file_config._input')
    def test_set_custom_bucket_name(self, _input, os):
        os.environ.get.return_value = 'mcgee'
        _input.return_value = 'booya'

        config = FileConfig()
        config.collect_settings(settings_to_get=['bucket'])
        eq_(config._parser.get('catsnap', 'bucket'), 'booya')

    @patch('catsnap.config.file_config.os')
    @patch('catsnap.config.file_config.getpass')
    @patch('catsnap.config.file_config._input')
    def test_change_config(self, _input, getpass, os):
        os.environ.__getitem__.return_value = 'mcgee'
        config = FileConfig()

        _input.side_effect = [ 'no',
                               'example.com' ]
        getpass.getpass.return_value = 'pa55word'

        config.collect_settings()
        _input.assert_has_calls([
                call("Would you like to print a fake file extension on urls? "),
                call("Enter the host for your catsnap api: ")])
        getpass.getpass.assert_has_calls([
                call('Enter your catsnap api key: ')])
        eq_(config._parser.get('catsnap', 'api_host'), 'example.com')
        with open(self.config_tempfile, 'r') as config_file:
            eq_(config_file.read(), """[catsnap]
extension = no
api_host = example.com
api_key = pa55word

""")

    @patch('catsnap.config.file_config.os')
    @patch('catsnap.config.file_config.getpass')
    @patch('catsnap.config.file_config._input')
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

    @patch('catsnap.config.file_config._input')
    def test_set_only_one_setting_name(self, _input):
        config = FileConfig()
        self._set_parser_defaults(config._parser)
        _input.return_value = 'truckit'

        config.collect_settings(settings_to_get=['bucket'])
        _input.assert_called_once_with("Please name your bucket (leave blank "
                "to use 'mypics'): ")
        eq_(config._parser.get('catsnap', 'bucket'), 'truckit')

class TestFileSetting(TestCase):
    @patch('catsnap.config.file_config._input')
    def test_input_patches_correctly(self, mock_input):
        setting = FileSetting(section='one',
                name='two',
                message='three',
                override_message='four')
        eq_(setting.read_method, mock_input)

    def test_sets_kwargs_as_attributes(self):
        setting = FileSetting(section='blue',
                name='red',
                message='green',
                override_message='greenish')
        eq_(setting.section, 'blue')
        eq_(setting.name, 'red')
        eq_(setting.message, 'green')
        eq_(setting.override_message, 'greenish')

    def test_invalid_args_cause_exception(self):
        def invalid_setting():
            FileSetting(extreme_ironing=True)

        assert_raises(TypeError, invalid_setting)

    def test_attributes_with_no_default_must_be_provided(self):
        def inadequate_setting():
            FileSetting()

        assert_raises(NotImplementedError, inadequate_setting)

