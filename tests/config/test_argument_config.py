from __future__ import unicode_literals

from mock import patch, call, Mock
from nose.tools import eq_, assert_raises, ok_
from tests import TestCase

from catsnap.config.argument_config import ArgumentConfig

class TestArgumentConfig(TestCase):
    @patch('argparse.ArgumentParser.error')
    @patch('catsnap.config.argument_config.sys')
    def test_getitem(self, sys, error):
        def _raise(message):
            raise Exception(message)
        error.side_effect = _raise
        sys.argv = ['catsnap', '--aws-access-key-id', 'itsme',
                '--bucket', 'robots', '--aws-secret-access-key', 'letmein',
                'add', 'http://example.com/image.jpg', 'tag1', 'tag2']

        config = ArgumentConfig()
        eq_(config['bucket'], 'robots')
        eq_(config['aws_access_key_id'], 'itsme')
        eq_(config['aws_secret_access_key'], 'letmein')
        eq_(config['arg'], ['add', 'http://example.com/image.jpg',
            'tag1', 'tag2'])
        assert_raises(KeyError, lambda: config['ripley <3 Jonesy'])

    @patch('catsnap.config.argument_config.sys')
    def test_getitem__when_there_are_no_arguments(self, sys):
        sys.argv = ['catsnap']
        config = ArgumentConfig()
        assert_raises(KeyError, lambda: config['bucket'])

    @patch('catsnap.config.argument_config.sys')
    def test_extension_is_not_present_if_not_provided(self, sys):
        sys.argv = ['catsnap']
        config = ArgumentConfig()
        ok_('extension' not in config)

    @patch('catsnap.config.argument_config.sys')
    def test_extension_is_true_if_turned_on(self, sys):
        sys.argv = ['catsnap', '--extension']
        config = ArgumentConfig()
        ok_('extension' in config)
        eq_(config['extension'], True)

    @patch('catsnap.config.argument_config.sys')
    def test_extension_is_false_if_turned_off(self, sys):
        sys.argv = ['catsnap', '--no-extension']
        config = ArgumentConfig()
        ok_('extension' in config)
        eq_(config['extension'], False)

    @patch('catsnap.config.argument_config.sys')
    def test_contains(self, sys):
        sys.argv = ['catsnap', '--bucket', 'robots']
        config = ArgumentConfig()
        ok_('bucket' in config)
        ok_('aws_access_key_id' not in config)
        ok_('brezhnev' not in config)

    def test_fails_if_it_does_not_know_about_a_setting_in_all_settings(self):
        with patch('catsnap.config.base.Config.ALL_SETTINGS', ['brofulness']):
            assert_raises(AttributeError, ArgumentConfig)
