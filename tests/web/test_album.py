import json
from io import StringIO
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
        body = json.loads(response.data.decode('utf-8'))
        assert 'album_id' in body, body

    @logged_in
    def test_whitespace_is_trimmed(self):
        response = self.app.post('/new_album.json', data={'name': ' photoz '})
        eq_(response.status_code, 200, response.data)

        session = Client().session()
        album = session.query(Album).one()
        eq_(album.name, 'photoz')

    @logged_in
    def test_album_names_must_be_unique(self):
        session = Client().session()
        session.add(Album(name='portrait sesh'))
        session.flush()

        response = self.app.post('/new_album.json',
                                 data={'name': 'portrait sesh'})
        eq_(response.status_code, 409, response.data)
        body = json.loads(response.data.decode('utf-8'))
        eq_(body['error'], "There is already an album with that name.")

    @with_settings(aws={'bucket': 'cattysnap'})
    def test_get_album_in_json_format(self):
        session = Client().session()
        album = Album(name='my pix')
        session.add(album)
        session.flush()

        cat = Image(album_id=album.album_id, filename='CA7')
        dog = Image(album_id=album.album_id, filename='D06')
        session.add(cat)
        session.add(dog)
        session.flush()

        response = self.app.get('/album/{0}.json'.format(album.album_id))
        eq_(response.status_code, 200, response.data)
        body = json.loads(response.data.decode('utf-8'))
        eq_(body, [
            {
                'page_url': '/image/{0}'.format(cat.image_id),
                'source_url': 'https://s3.amazonaws.com/cattysnap/CA7',
                'caption': 'CA7'
            },
            {
                'page_url': '/image/{0}'.format(dog.image_id),
                'source_url': 'https://s3.amazonaws.com/cattysnap/D06',
                'caption': 'D06'
            },
        ])

