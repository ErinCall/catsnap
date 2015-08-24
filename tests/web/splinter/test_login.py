from __future__ import unicode_literals

from tests import with_settings
from tests.web.splinter import TestCase, logged_in
from catsnap import Client
from catsnap.table.image import Image
from catsnap.table.album import Album


class TestLoggedInDisplay(TestCase):
    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_on_view_image(self):
        session = Client().session()
        image = Image(filename='bab1eface', title='face of a baby')
        session.add(image)
        session.flush()
        self.visit_url('/image/{0}'.format(image.image_id))
        assert self.browser.is_text_present('Log out'), \
            "Page didn't act like logged in"

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_on_view_album(self):
        session = Client().session()
        album = Album(name="fotozzzz")
        session.add(album)
        session.flush()
        self.visit_url('/album/{0}'.format(album.album_id))
        assert self.browser.is_text_present('Log out'), \
            "Page didn't act like logged in"
