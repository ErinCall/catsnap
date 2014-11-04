from __future__ import unicode_literals

import time
from tests import TestCase
from catsnap import Client
from nose.tools import eq_
from mock import patch

from catsnap.table.image import Image
from catsnap.table.album import Album

class TestAlbums(TestCase):
    @patch('catsnap.table.created_at_bookkeeper.time')
    def test_created_at_is_set_at_creation_time(self, mock_time):
        now = time.strptime('2011-05-09 13:01:01', '%Y-%m-%d %H:%M:%S')
        mock_time.strftime = time.strftime
        mock_time.gmtime.return_value = now
        session = Client().session()
        album = Album(name='my pix')
        session.add(album)
        session.flush()

        eq_(album.created_at, '2011-05-09 13:01:01')

    def test_find_all_images_in_an_album(self):
        session = Client().session()
        album = Album(name='my pix')
        session.add(album)
        session.flush()
        session.add(Image(album_id = album.album_id, filename='deadbeef'))
        session.add(Image(album_id = album.album_id, filename='badcafe'))
        session.add(Image(album_id = None, filename='cafebabe'))

        images = Album.images_for_album_id(album.album_id)
        eq_(['deadbeef', 'badcafe'],
                map(lambda x: x.filename, images))
