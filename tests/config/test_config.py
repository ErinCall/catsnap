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

    @patch('catsnap.config.os')
    def test_fetch_dot_separated_value_from_environment(self, mock_os):
        mock_os.environ = {
            'CATSNAP_ERROR_EMAIL_PROVIDER_HOSTNAME': 'smtp.ema.il'
        }

        eq_(Config()['error_email.provider.hostname'], 'smtp.ema.il')

    def test_fake_settings_cause_an_error(self):
        assert_raises(AttributeError, lambda: Config()['time_signature'])

    @patch('catsnap.config.os')
    def test_fetch_value_from_yaml_structure(self, mock_os):
        mock_os.environ = {}
        Config()._contents = {
            'postgres_url': 'postgresql://localhost/catsnap'
        }

        eq_(Config()['postgres_url'], 'postgresql://localhost/catsnap')

    @patch('catsnap.config.os')
    def test_fech_dot_separated_value_from_yaml_structure(self, mock_os):
        mock_os.environ = {}
        Config()._contents = {
            'aws': {
                'bucket': 'do-not-go-into-the-dog-park'
            }
        }

        eq_(Config()['aws.bucket'], 'do-not-go-into-the-dog-park')
