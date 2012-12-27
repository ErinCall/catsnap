from __future__ import unicode_literals

import json
from mock import patch, Mock
from tests import TestCase, with_settings
from nose.tools import eq_
from catsnap import Client
from catsnap.table.image import Image

class TestIndex(TestCase):
    def test_requires_login(self):
        response = self.app.post('/add', data={})
        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'], 'http://localhost/')

    @patch('catsnap.web.controllers.add.g')
    @patch('catsnap.web.controllers.add.ImageTruck')
    def test_add_a_tag(self, ImageTruck, g):
        truck = Mock()
        ImageTruck.new_from_url.return_value = truck
        truck.calculate_filename.return_value = 'CA7'
        truck.url.return_value = 'ess three'

        response = self.app.post('/add', data={
                'add_tags': 'pet cool',
                'url': 'imgur.com/cool_cat.gif'})
        eq_(response.status_code, 200, response.data)
        assert '<a href="ess three">ess three</a>' in response.data, response.data

        session = Client().session()
        images = session.query(Image.filename, Image.source_url).all()
        eq_(images, [('CA7', 'imgur.com/cool_cat.gif')])

    @patch('catsnap.web.controllers.add.g')
    @patch('catsnap.web.controllers.add.ImageTruck')
    def test_with_json_format(self, ImageTruck, g):
        truck = Mock()
        ImageTruck.new_from_url.return_value = truck
        truck.calculate_filename.return_value = 'CA7'
        truck.url.return_value = 'ess three'
        response = self.app.post('/add', data={
                'add_tags': 'pet cool',
                'url': 'imgur.com/cool_cat.gif'})

        response = self.app.post('/add.json', data={
            'add_tags': 'pet cool',
            'url': 'imgur.com/cool_cat.gif'})
        eq_(response.status_code, 200, response.data)
        body = json.loads(response.data)
        eq_(body, {'url': 'ess three'})
