from __future__ import unicode_literals

import time
import datetime
import sha
from StringIO import StringIO
from mock import patch, Mock
from tests import TestCase, with_settings
from nose.tools import eq_
from catsnap import Client
from catsnap.table.image import Image

class TestAuth(TestCase):
    @with_settings(api_key='supersekrit')
    @patch('catsnap.web.controllers.add.ImageTruck')
    def test_hmac_auth(self, ImageTruck):
        truck = Mock()
        ImageTruck.new_from_url.return_value = truck
        truck.calculate_filename.return_value = 'CA7'
        truck.url.return_value = 'ess three'
        now = str(datetime.datetime.utcnow())
        string_to_sign = "%s\n%s" % (now, Client().config().api_key)
        signature = sha.sha(string_to_sign).hexdigest()

        response = self.app.post('/add',
                headers=[
                    ('X-Catsnap-Signature', signature),
                    ('X-Catsnap-Signature-Date', now)],
                data={'tags': 'pet cool',
                    'album': '',
                    'url': 'http://imgur.com/cat.gif'})
        eq_(response.status_code, 200, response.data)

    @with_settings(api_key='supersekrit')
    def test_hmac_auth__fails_if_signature_does_not_match(self):
        now = str(datetime.datetime.utcnow())
        response = self.app.post('/add',
                headers=[
                    ('X-Catsnap-Signature', 'MALISHUS'),
                    ('X-Catsnap-Signature-Date', now)],
                data={'tags': 'pet cool', 'url': 'http://imgur.com/cat.gif'})
        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'], 'http://localhost/')

    @with_settings(api_key='supersekrit')
    def test_hmac_auth__fails_if_given_time_does_not_match_server_time(self):
        then = '1984-03-14 07:45:22.0'
        string_to_sign = "%s\n%s" % (then, Client().config().api_key)
        signature = sha.sha(string_to_sign).hexdigest()

        response = self.app.post('/add',
                headers=[
                    ('X-Catsnap-Signature', signature),
                    ('X-Catsnap-Signature-Date', then)],
                data={'tags': 'pet cool', 'url': 'http://imgur.com/cat.gif'})
        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'], 'http://localhost/')
