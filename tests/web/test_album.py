from __future__ import unicode_literals

import json
from StringIO import StringIO
from mock import patch, Mock
from tests import TestCase, with_settings
from nose.tools import eq_
from catsnap import Client
from catsnap.table.album import Album

class TestAlbum(TestCase):
    def test_new_album_requires_login(self):
        response = self.app.post('/new_album', data={'name': 'malicious'})
        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'], 'http://localhost/')

    def test_get_the_new_album_page(self):
        response = self.app.get('/new_album')
        eq_(response.status_code, 200)

    @patch('catsnap.web.controllers.album.g')
    def test_add_an_album(self, g):
        response = self.app.post('/new_album', data={'name': 'my pics'})
        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'], 'http://localhost/add')

        session = Client().session()
        albums = session.query(Album.name).all()
        eq_(albums, [('my pics',)])

    @patch('catsnap.web.controllers.album.g')
    def test_add_an_album__with_json_format(self, g):
        response = self.app.post('/new_album.json', data={'name': 'my pics'})
        eq_(response.status_code, 200, response.data)
        body = json.loads(response.data)
        assert 'album_id' in body, body

