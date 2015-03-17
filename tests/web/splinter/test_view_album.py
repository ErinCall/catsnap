from __future__ import unicode_literals

from tests import with_settings
from tests.web.splinter import TestCase
from catsnap import Client
from catsnap.table.image import Image
from catsnap.table.album import Album
from nose.tools import eq_

class TestViewAlbum(TestCase):
    @with_settings(bucket='humptydump')
    def test_view_an_album(self):
        session = Client().session()

        album = Album(name="photo sesh")
        session.add(album)
        session.flush()

        silly = Image(album_id=album.album_id, filename="silly")
        serious = Image(album_id=album.album_id, filename="serious")
        session.add(silly)
        session.add(serious)
        session.flush()

        self.visit_url('/album/{0}'.format(album.album_id))

        images = self.browser.find_by_tag('img')
        eq_(map(lambda i: i['src'], images), [
            'https://s3.amazonaws.com/humptydump/silly',
            'https://s3.amazonaws.com/humptydump/serious',
        ])
        eq_(map(lambda i: i['alt'], images), ['silly', 'serious'])

        assert self.browser.is_text_present('silly')
        assert self.browser.is_text_present('serious')
