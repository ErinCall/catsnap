from __future__ import unicode_literals

import json
from StringIO import StringIO
from mock import patch, Mock
from tests import TestCase, logged_in
from nose.tools import eq_
from catsnap import Client
from catsnap.table.image import Image
from catsnap.table.image_tag import ImageTag
from catsnap.table.tag import Tag


class TestAdd(TestCase):
    def test_adding_requires_login(self):
        response = self.app.post('/add', data={})
        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'], 'http://localhost/')

    def test_get_the_add_page(self):
        response = self.app.get('/add')
        eq_(response.status_code, 200)

    @logged_in
    @patch('catsnap.web.controllers.image.ImageMetadata')
    @patch('catsnap.web.controllers.image.ResizeImage')
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_add_a_tag(self, ImageTruck, ResizeImage, ImageMetadata):
        truck = Mock()
        ImageTruck.new_from_url.return_value = truck
        truck.calculate_filename.return_value = 'CA7'
        truck.url.return_value = 'ess three'

        response = self.app.post('/add', data={
            'album': '',
            'tags': 'pet cool',
            'url': 'imgur.com/cool_cat.gif'})

        session = Client().session()
        image = session.query(Image).one()
        eq_(image.filename, 'CA7')
        eq_(image.source_url, 'imgur.com/cool_cat.gif')

        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'],
            'http://localhost/image/%d' % image.image_id)

    @logged_in
    @patch('catsnap.web.controllers.image.ImageMetadata')
    @patch('catsnap.web.controllers.image.ResizeImage')
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_upload_an_image(self, ImageTruck, ResizeImage, ImageMetadata):
        truck = Mock()
        ImageTruck.new_from_stream.return_value = truck
        truck.calculate_filename.return_value = 'CA7'
        truck.url.return_value = 'ess three'
        ImageMetadata.image_metadata.return_value = {
            'camera': 'Samsung NX210',
            'photographed_at': '2013-05-09 12:00:00',
            'focal_length': 30,
            'aperture': '1/1.8',
            'shutter_speed': 5,
            'iso': '400'}

        response = self.app.post('/add', data={
            'album': '',
            'tags': 'pet cool',
            'url': '',
            'title': 'My cat being awesome',
            'description': 'my cat is awesome. You can see how awesome.',
            'file': (StringIO(str('booya')), 'img.jpg')})

        session = Client().session()
        image = session.query(Image).one()

        eq_(image.filename, 'CA7')
        eq_(image.source_url, '')
        eq_(image.title, 'My cat being awesome')
        eq_(image.description, 'my cat is awesome. You can see how awesome.')

        ResizeImage.make_resizes.assert_called_with(image, truck)

        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'],
            'http://localhost/image/%d' % image.image_id)

    @logged_in
    @patch('catsnap.web.controllers.image.ResizeImage')
    @patch('catsnap.web.controllers.image.ImageMetadata')
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_upload_an_image_twice(self,
                                   ImageTruck,
                                   ImageMetadata,
                                   ResizeImage):
        truck = Mock()
        ImageTruck.new_from_stream.return_value = truck
        truck.calculate_filename.return_value = 'CA7'
        truck.calculate_filename.return_value = 'CA7'
        truck.url.return_value = 'ess three'
        ImageMetadata.image_metadata.return_value = {}

        response = self.app.post('/add', data={
            'tags': 'pet',
            'url': '',
            'album': '',
            'file': (StringIO(str('booya')), 'img.jpg')})
        eq_(response.status_code, 302)
        response = self.app.post('/add', data={
            'tags': 'pet',
            'url': '',
            'album': '',
            'file': (StringIO(str('booya')), 'img.jpg')})
        eq_(response.status_code, 302)

        session = Client().session()
        image = session.query(Image).one()
        image_tags = session.query(ImageTag.image_id).all()
        eq_(image_tags, [(image.image_id,)])

    @logged_in
    @patch('catsnap.web.controllers.image.ImageMetadata')
    @patch('catsnap.web.controllers.image.ResizeImage')
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_with_json_format(self, ImageTruck, ResizeImage, ImageMetadata):
        truck = Mock()
        ImageTruck.new_from_url.return_value = truck
        truck.calculate_filename.return_value = 'CA7'
        truck.url.return_value = 'ess three'
        ImageMetadata.image_metadata.return_value = {}

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
