from __future__ import unicode_literals

from mock import patch, call, Mock
from nose.tools import eq_
from tests import TestCase

from catsnap import Config

class TestConfig(TestCase):
    @patch('catsnap.Config._input')
    @patch('catsnap.getpass')
    @patch('catsnap.sys')
    def test_get_credentials(self, sys, getpass, _input):
        getpass.getpass.return_value = 'secret access key'
        _input.return_value = 'access key id'

        config = Config()
        config.get_settings()
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
        config.get_settings()
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
        config.get_settings()
        eq_(config.parser.get('catsnap', 'bucket'), 'booya')
        eq_(config.parser.get('catsnap', 'table_prefix'), 'booya')

    @patch('catsnap.Config.get_credentials')
    @patch('catsnap.Config.get_config')
    def test_create_config_withut_setting_up(self, get_config,
            get_credentials):
        config = Config()
        assert not get_credentials.called
        assert not get_config.called

    @patch('catsnap.os')
    @patch('catsnap.getpass')
    @patch('catsnap.Config._input')
    def test_change_config(self, _input, getpass, os):
        os.environ.__getitem__.return_value = 'mcgee'
        config = Config()
        self._set_parser_defaults(config.parser)

        _input.side_effect = [ 'hereiam', 'catsnap-giggity' ]
        getpass.getpass.return_value = 'pa55word'

        config.get_settings(override_existing=True)
        _input.assert_has_calls([
                call("Enter your access key id (leave blank to keep using "
                        "'itsme'): "),
                call("Please name your bucket (leave blank to use "
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
        config = Config()
        self._set_parser_defaults(config.parser)

        _input.return_value = ''
        getpass.getpass.return_value = ''

        config.get_settings(override_existing=True)
        eq_(config.parser.get('Credentials', 'aws_access_key_id'), 'itsme')
        eq_(config.parser.get('Credentials', 'aws_secret_access_key'), 'letmein')
        eq_(config.parser.get('catsnap', 'bucket'), 'mypics')
        eq_(config.parser.get('catsnap', 'table_prefix'), 'mypics')

    @patch('catsnap.Config._input')
    def test_change_config__one_setting_name(self, _input):
        config = Config()
        self._set_parser_defaults(config.parser)
        _input.return_value = 'truckit'

        config.get_settings(override_existing=True, settings=['bucket'])
        _input.assert_called_once_with("Please name your bucket (leave blank "
                "to use 'mypics'): ")
        eq_(config.parser.get('catsnap', 'bucket'), 'truckit')

    @patch('catsnap.Config.get_credentials')
    @patch('catsnap.Config.get_config')
    def test_get_settings__passes_setting_names_along(self, get_config,
            get_credentials):
        config = Config()
        config.parser = Mock()
        config.get_settings(override_existing=True, settings=[
                'bucket'])
        get_config.assert_called_once_with(['bucket'], override_existing=True)
        get_credentials.assert_called_once_with(['bucket'],
                override_existing=True)

    @patch('catsnap.Config._input')
    def test_change_config__does_not_override_custom_table_prefix(self, _input):
        existing_settings = {
                'bucket': 'im-ah-gezz',
                'table_prefix': 'that-catsnap-thing'}
        def get_setting(section, setting_name):
            if section != 'catsnap':
                raise ValueError(section)
            return existing_settings[setting_name]
        config = Config()
        config.parser = Mock()
        config.parser.get.side_effect = get_setting
        config.parser.has_option.return_value = True
        _input.return_value = 'pics'

        config.get_config(['bucket'], override_existing=True)
        config.parser.set.assert_called_once_with('catsnap', 'bucket', 'pics')

    def _set_parser_defaults(self, parser):
        parser.add_section('Credentials')
        parser.add_section('catsnap')
        parser.set('Credentials', 'aws_access_key_id', 'itsme')
        parser.set('Credentials', 'aws_secret_access_key', 'letmein')
        parser.set('catsnap', 'bucket', 'mypics')
        parser.set('catsnap', 'table_prefix', 'mypics')

