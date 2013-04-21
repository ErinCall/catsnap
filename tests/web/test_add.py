from __future__ import unicode_literals

import json
from StringIO import StringIO
from mock import patch, Mock
from tests import TestCase, with_settings, logged_in
from nose.tools import eq_
from catsnap import Client
from catsnap.table.image import Image

class TestAdd(TestCase):
    def test_adding_requires_login(self):
        response = self.app.post('/add', data={})
        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'], 'http://localhost/')

    def test_get_the_add_page(self):
        response = self.app.get('/add')
        eq_(response.status_code, 200)

    @logged_in
    @patch('catsnap.web.controllers.add.ImageTruck')
    def test_add_a_tag(self, ImageTruck):
        truck = Mock()
        ImageTruck.new_from_url.return_value = truck
        truck.calculate_filename.return_value = 'CA7'
        truck.url.return_value = 'ess three'

        response = self.app.post('/add', data={
                'album': '',
                'tags': 'pet cool',
                'url': 'imgur.com/cool_cat.gif'})
        eq_(response.status_code, 200, response.data)
        assert '<a href="ess three">pet cool</a>' in response.data, response.data

        session = Client().session()
        images = session.query(Image.filename, Image.source_url).all()
        eq_(images, [('CA7', 'imgur.com/cool_cat.gif')])

    @logged_in
    @patch('catsnap.web.controllers.add.ImageTruck')
    def test_upload_an_image(self, ImageTruck):
        truck = Mock()
        ImageTruck.new_from_stream.return_value = truck
        truck.calculate_filename.return_value = 'CA7'
        truck.url.return_value = 'ess three'

        response = self.app.post('/add', data={
                'album': '',
                'tags': 'pet cool',
                'url': '',
                'title': 'My cat being awesome',
                'description': 'my cat is awesome. You can see how awesome.',
                'file': (StringIO('booya'), 'img.jpg')})
        eq_(response.status_code, 200)

        session = Client().session()
        images = session.query(Image.filename,
                               Image.source_url,
                               Image.title,
                               Image.description).all()
        eq_(images, [('CA7',
                      '',
                      'My cat being awesome',
                      'my cat is awesome. You can see how awesome.')])

    @logged_in
    @patch('catsnap.web.controllers.add.ImageTruck')
    def test_with_json_format(self, ImageTruck):
        truck = Mock()
        ImageTruck.new_from_url.return_value = truck
        truck.calculate_filename.return_value = 'CA7'
        truck.url.return_value = 'ess three'

        response = self.app.post('/add.json', data={
            'album': '',
            'tags': 'pet cool',
            'url': 'imgur.com/cool_cat.gif'})
        eq_(response.status_code, 200, response.data)
        body = json.loads(response.data)
        eq_(body, {'url': 'ess three'})

    @logged_in
    def test_returns_bad_request_if_no_image_provided(self):
        response = self.app.post('/add', data={
            'url': '',
            'image_file': (StringIO(), ''),
            'tags': 'pet cool'})
        eq_(response.status_code, 400)
