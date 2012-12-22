from __future__ import unicode_literals

from mock import patch, call, Mock
from nose.tools import eq_, assert_raises
from tests import TestCase

from catsnap.config import MetaConfig

class TestMetaConfig(TestCase):
    def test_getitem_delegates_to_subconfigs(self):
        env_config = {'number 5': 'is alive'}
        file_config = {'number 7': 'I am'}
        config = MetaConfig()
        config._env_config = env_config
        config._file_config = file_config
        eq_(config['number 5'], 'is alive')
        eq_(config['number 7'], 'I am')

    def test_nonexistent_items_cause_an_error(self):
        config = MetaConfig()
        config._argument_config = {}
        config._env_config = {}
        config._file_config = {}
        try:
            config['rausch']
        except KeyError as e:
            eq_(e.message, "Couldn't find any setting at all for 'rausch'. "
                    "You'll need to supply it in some way--try `catsnap "
                    "config`, or see the docs for other ways to supply "
                    "a setting.")
        else:
            raise AssertionError('this test shoulda thrown')

    def test_getattr_delegates_to_getitem(self):
        config = MetaConfig()
        config._env_config = {'aws_access_key_id': 'itsme'}

        eq_(config.aws_access_key_id, 'itsme')

    def test_getattr_raises_for_unknown_settings(self):
        config = MetaConfig()

        assert_raises(AttributeError, lambda: config.number_5)

    def test_noncompulsory_arguments_have_defaults(self):
        config = MetaConfig()
        eq_(config['extension'], False)
