from __future__ import unicode_literals
from mock import Mock

import catsnap

class TestCase():

    def setUp(self):
        catsnap.Config._input = Mock()
        catsnap.getpass = Mock()
