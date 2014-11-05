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

    def test_images_for_album_id_sorts_by_photographed_then_added_date(self):
        session = Client().session()
        album = Album(name='my pix')
        session.add(album)
        session.flush()

        han = Image(
            photographed_at='2012-05-13 03:00:00',
            album_id=album.album_id,
            filename="han",
        )
        han.created_at = '2014-11-22 13:15:00'
        greedo = Image(
            photographed_at='2014-12-28 15:24:00',
            album_id=album.album_id,
            filename="greedo",
        )
        greedo.created_at = '2014-08-01 08:00:00'
        artoo = Image(
            photographed_at=None,
            album_id=album.album_id,
            filename="R2D2",
        )
        artoo.created_at = '1977-05-13 01:00:00'
        session.add(han)
        session.add(greedo)
        session.add(artoo)
        session.flush()

        # Sorting should be done by the date the image was shot, or the date
        # it was added if it has no photographed_at. Han shot first, so he
        # should show up before greedo. Artoo never shot at all, so use his
        # created_at (which refers to the *record*, not the image) instead.
        images = Album.images_for_album_id(album.album_id)
        eq_(['R2D2', 'han', 'greedo'],
                map(lambda x: x.filename, images))
