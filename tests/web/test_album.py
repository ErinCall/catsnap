from __future__ import unicode_literals

import json
from StringIO import StringIO
from mock import patch, Mock
from tests import TestCase, with_settings, logged_in
from nose.tools import eq_
from catsnap import Client
from catsnap.table.album import Album
from catsnap.table.image import Image

class TestAlbum(TestCase):
    def test_new_album_requires_login(self):
        response = self.app.post('/new_album', data={'name': 'malicious'})
        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'], 'http://localhost/')

    def test_get_the_new_album_page(self):
        response = self.app.get('/new_album')
        eq_(response.status_code, 200)

    @logged_in
    def test_add_an_album(self):
        response = self.app.post('/new_album', data={'name': 'my pics'})
        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'], 'http://localhost/add')

        session = Client().session()
        albums = session.query(Album.name).all()
        eq_(albums, [('my pics',)])

    @logged_in
    def test_add_an_album__with_json_format(self):
        response = self.app.post('/new_album.json', data={'name': 'my pics'})
        eq_(response.status_code, 200, response.data)
        body = json.loads(response.data)
        assert 'album_id' in body, body

    @with_settings(bucket='cattysnap')
    def test_view_an_album(self):
        session = Client().session()
        album = Album(name='my pix')
        session.add(album)
        session.flush()
        cat = Image(album_id=album.album_id, filename='CA7')
        session.add(cat)
        dog = Image(album_id=album.album_id, filename='D06')
        session.add(dog)
        not_in_album = Image(album_id=None, filename='deadbeef')
        session.add(not_in_album)
        session.flush()

        response = self.app.get('/album/%d' % album.album_id)
        link = '<a href="/image/%d">'
        cat_link = link % cat.image_id
        dog_link = link % dog.image_id
        assert cat_link in response.data, response.data
        assert dog_link in response.data, response.data
        assert 'my pix' in response.data, response.data

