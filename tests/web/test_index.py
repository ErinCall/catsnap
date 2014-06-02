from __future__ import unicode_literals

import re

from tests import TestCase
from nose.tools import eq_

from catsnap.table.album import Album
from catsnap import Client

class TestIndex(TestCase):
    def test_get_index(self):
        session = Client().session()

        session.add(Album(name='hurdygurdy'))
        session.add(Album(name='dordybordy'))

        response = self.app.get('/')
        eq_(response.status_code, 200)

        body = response.data
        body = re.sub(r'hurdygurdy.*', '', body, flags=re.DOTALL)

        assert re.search(r'dordybordy', body) is not None, \
               'dordybordy should have come before hurdygurdy'
