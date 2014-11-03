from __future__ import unicode_literals

import json
from StringIO import StringIO
from mock import patch, Mock, call
from tests import TestCase, logged_in
from nose.tools import eq_
from catsnap import Client
from catsnap.table.image import Image, ImageContents
from catsnap.table.album import Album


class TestAdd(TestCase):
    def test_adding_requires_login(self):
        response = self.app.post('/add', data={})
        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'], 'http://localhost/')

    @logged_in
    def test_get_the_add_page(self):
        response = self.app.get('/add')
        eq_(response.status_code, 200)

    @logged_in
    @patch('catsnap.web.controllers.image.process_image')
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_upload_an_image(self, ImageTruck, process_image):
        truck = Mock()
        ImageTruck.new_from_stream.return_value = truck
        truck.filename = 'CA7'
        truck.url.return_value = 'ess three'
        truck.contents = b''
        truck.content_type = "image/jpeg"

        session = Client().session()
        album = Album(name='11:11 Eleven Eleven')
        session.add(album)
        session.flush()

        response = self.app.post('/add', data={
            'url': '',
            'album_id': album.album_id,
            'file': (StringIO(str('booya')), 'img.jpg')})

        image = session.query(Image).one()

        eq_(image.filename, 'CA7')
        eq_(image.source_url, '')
        eq_(image.album_id, album.album_id)

        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'],
            'http://localhost/image/{0}'.format(image.image_id))

        contents = session.query(ImageContents).one()
        eq_(image.image_id, contents.image_id)

        process_image.delay.assert_called_with(contents.image_contents_id)

    @logged_in
    @patch('catsnap.web.controllers.image.process_image')
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_upload_an_image_twice(self, ImageTruck, process_image):
        truck = Mock()
        ImageTruck.new_from_stream.return_value = truck
        truck.filename = 'CA7'
        truck.url.return_value = 'ess three'
        truck.contents = b''
        truck.content_type = "image/jpeg"

        response = self.app.post('/add', data={
            'url': '',
            'file': (StringIO(str('booya')), 'img.jpg')})
        eq_(response.status_code, 302)
        response = self.app.post('/add', data={
            'url': '',
            'file': (StringIO(str('booya')), 'img.jpg')})
        eq_(response.status_code, 302)

        session = Client().session()
        image = session.query(Image).one()
        contentses = session.query(ImageContents).all()
        for contents in contentses:
            eq_(contents.image_id, image.image_id)
        contents_calls = map(lambda x: call(x.image_contents_id), contentses)
        process_image.delay.assert_has_calls(contents_calls)

    @logged_in
    @patch('catsnap.web.controllers.image.process_image')
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_upload_an_image_with_json_format(self, ImageTruck, process_image):
        truck = Mock()
        ImageTruck.new_from_url.return_value = truck
        truck.filename = 'CA741C'
        truck.url.return_value = 'cloudfrunt.nut/CA741C'
        truck.contents = b''
        truck.content_type = "image/gif"

        response = self.app.post('/add.json', data={
            'album': '',
            'tags': 'pet cool',
            'url': 'imgur.com/cool_cat.gif'})
        eq_(response.status_code, 200, response.data)

        session = Client().session()
        image = session.query(Image).one()
        body = json.loads(response.data)

        eq_(body, {'url': 'cloudfrunt.nut/CA741C', 'image_id': image.image_id})
        contents = session.query(ImageContents).one()
        eq_(contents.image_id, image.image_id)
        process_image.delay.assert_called_with(contents.image_contents_id)

    @logged_in
    def test_returns_bad_request_if_no_image_provided(self):
        response = self.app.post('/add', data={
            'url': '',
            'image_file': (StringIO(), ''),
            'tags': 'pet cool'})
        eq_(response.status_code, 400)
