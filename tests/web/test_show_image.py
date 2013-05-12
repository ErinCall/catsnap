from __future__ import unicode_literals

import json
from tests import TestCase, with_settings
from nose.tools import eq_
from catsnap import Client
from catsnap.table.image import Image
from catsnap.table.album import Album

class TestShowImage(TestCase):
    @with_settings(bucket='snapcats')
    def test_view_an_image(self):
        session = Client().session()
        album = Album(name='cow shots')
        session.add(album)
        image = Image(filename='deadbeef',
                      description='one time I saw a dead cow',
                      title='dead beef',
                      album_id=album.album_id)

        session.add(image)
        session.flush()

        response = self.app.get('/image/%d' % image.image_id)
        assert 'https://s3.amazonaws.com/snapcats/deadbeef' in response.data,\
                response.data

    @with_settings(bucket='snapcats')
    def test_get_image_info_as_json(self):
        session = Client().session()
        album = Album(name='cow shots')
        session.add(album)
        session.flush()
        image = Image(filename='deadbeef',
                      description='one time I saw a dead cow',
                      title='dead beef',
                      album_id=album.album_id)

        session.add(image)
        image.add_tags(['cow', 'dead'])
        session.flush()

        response = self.app.get('/image/%d.json' % image.image_id)
        eq_(json.loads(response.data), {
            'description': 'one time I saw a dead cow',
            'title': 'dead beef',
            'album_id': album.album_id,
            'tags': [ 'cow', 'dead', ],
            'source_url': 'https://s3.amazonaws.com/snapcats/deadbeef',
            'camera': None,
            'photographed_at': None,
            'focal_length': None,
            'aperture': None,
            'shutter_speed': None,
            'iso': None,
            })
