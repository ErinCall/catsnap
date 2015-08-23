from __future__ import unicode_literals

from mock import patch, call, Mock
from nose.tools import eq_, ok_, assert_raises
from tests import TestCase
from ConfigParser import ConfigParser

from catsnap.config.file_config import FileConfig, FileSetting

class TestFileConfig(TestCase):
    def _set_parser_defaults(self, parser):
        parser.add_section('Credentials')
        parser.add_section('catsnap')
        parser.set('Credentials', 'aws_access_key_id', 'itsme')
        parser.set('Credentials', 'aws_secret_access_key', 'letmein')
        parser.set('catsnap', 'bucket', 'mypics')

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

class TestFileSetting(TestCase):
    def test_sets_kwargs_as_attributes(self):
        setting = FileSetting(section='blue', name='red')
        eq_(setting.section, 'blue')
        eq_(setting.name, 'red')

    def test_invalid_args_cause_exception(self):
        def invalid_setting():
            FileSetting(extreme_ironing=True)

        assert_raises(TypeError, invalid_setting)

    def test_attributes_with_no_default_must_be_provided(self):
        def inadequate_setting():
            FileSetting()

        assert_raises(NotImplementedError, inadequate_setting)

