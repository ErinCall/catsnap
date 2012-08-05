from __future__ import unicode_literals

from mock import MagicMock
import tempfile

import catsnap
import catsnap.config.file_config

class TestCase():

    def setUp(self):
        (_, creds) = tempfile.mkstemp()
        self.creds_tempfile = creds
        (_, config) = tempfile.mkstemp()
        self.config_tempfile = config
        catsnap.config.file_config.FileConfig._input = MagicMock()
        catsnap.config.file_config.CONFIG_FILE = config
        catsnap.config.file_config.LEGACY_CREDENTIALS_FILE = creds

        catsnap.config.argument_config.sys = MagicMock()

        catsnap.config.file_config.getpass = MagicMock()

    def tearDown(self):
        catsnap.config.MetaConfig._instance = None
        catsnap.Client._instance = None
