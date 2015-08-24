from __future__ import unicode_literals

import json
from tests import TestCase, with_settings
from nose.tools import eq_
from catsnap import Client
from catsnap.table.image import Image, ImageResize
from catsnap.table.album import Album

class TestShowImage(TestCase):
    @with_settings(aws={'bucket': 'snapcats'})
    def test_view_an_image(self):
        session = Client().session()
        album = Album(name='cow shots')
        session.add(album)
        session.flush()
        prev_image = Image(filename='badcafe',
                           album_id=album.album_id)
        session.add(prev_image)
        image = Image(filename='deadbeef',
                      description='one time I saw a dead cow',
                      title='dead beef',
                      album_id=album.album_id)
        session.add(image)
        next_image = Image(filename='dadface',
                           album_id=album.album_id)
        session.add(next_image)
        session.flush()

        response = self.app.get('/image/%d' % image.image_id)
        assert 'https://s3.amazonaws.com/snapcats/deadbeef' in response.data,\
                response.data

        assert 'one time I saw a dead cow' in response.data, response.data
        assert 'cow shots' in response.data, response.data
        assert str(prev_image.image_id) in response.data, response.data
        assert str(next_image.image_id) in response.data, response.data

    @with_settings(aws={'bucket': 'snapcats'})
    def test_view_an_image__defaults_to_medium(self):
        session = Client().session()
        image = Image(filename='deadbeef',
                      description='one time I saw a dead cow',
                      title='dead beef')
        session.add(image)
        session.flush()

        for (size, suffix) in [(100, 'thumbnail'), (320, 'small'), (500, 'medium'), (1600, 'large')]:
            session.add(ImageResize(image_id=image.image_id, width=size, height=size, suffix=suffix))
        session.flush()

        response = self.app.get('/image/%d' % image.image_id)
        assert 'https://s3.amazonaws.com/snapcats/deadbeef_medium' in response.data,\
                response.data

    # if no medium exists, assume it's because the original is smaller than a
    # "medium," and thus the original is an appropriate size.
    @with_settings(aws={'bucket': 'snapcats'})
    def test_view_an_image__defaults_to_original_if_no_medium_exists(self):
        session = Client().session()
        image = Image(filename='deadbeef',
                      description='one time I saw a dead cow',
                      title='dead beef')
        session.add(image)
        session.flush()

        for (size, suffix) in [(100, 'thumbnail'), (320, 'small')]:
            session.add(ImageResize(image_id=image.image_id, width=size, height=size, suffix=suffix))
        session.flush()

        response = self.app.get('/image/%d' % image.image_id)
        assert 'src="https://s3.amazonaws.com/snapcats/deadbeef"' in response.data,\
                response.data

    @with_settings(aws={'bucket': 'snapcats'})
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
