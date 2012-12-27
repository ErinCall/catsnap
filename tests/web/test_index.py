from __future__ import unicode_literals

from tests import TestCase
from nose.tools import eq_

class TestIndex(TestCase):
    def test_get_index(self):
        response = self.app.get('/')
        eq_(response.status_code, 200)
