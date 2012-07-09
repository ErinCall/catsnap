from __future__ import unicode_literals
from mock import Mock

import catsnap
import tempfile

class TestCase():

    def setUp(self):
        (_, creds) = tempfile.mkstemp()
        (_, config) = tempfile.mkstemp()
        catsnap.Config._input = Mock()
        catsnap.Config.CONFIG_FILE = config
        catsnap.Config.CREDENTIALS_FILE = creds
        catsnap.getpass = Mock()
