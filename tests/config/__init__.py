from __future__ import unicode_literals

from mock import patch, call, Mock
from nose.tools import eq_, assert_raises
from tests import TestCase

from catsnap.config import Config

class TestConfig(TestCase):
    @patch('catsnap.config.os')
    def test_fetch_value_from_environment(self, mock_os):
        mock_os.environ = {
            'CATSNAP_POSTGRES_URL': 'postgresql://localhost/catsnap'
        }

        eq_(Config()['postgres_url'], 'postgresql://localhost/catsnap')
