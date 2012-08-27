from __future__ import unicode_literals

from mock import patch, call, Mock
from nose.tools import eq_, assert_raises, ok_
from tests import TestCase

from catsnap.config.env_config import EnvConfig

class TestEnvConfig(TestCase):
    @patch('catsnap.config.env_config.os')
    def test_getitem(self, os):
        os.environ = {'CATSNAP_SPARTACUS': 'cancellara'}
        config = EnvConfig()

        eq_(config['spartacus'], 'cancellara')
        assert_raises(KeyError, lambda: config['failure'])

    @patch('catsnap.config.env_config.os')
    def test_contains(self, os):
        os.environ = {'CATSNAP_SHUT_UP': 'legs'}
        config = EnvConfig()

        ok_('shut_up' in config)
        ok_('abandon' not in config)
