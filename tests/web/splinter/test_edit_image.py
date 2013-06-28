from __future__ import unicode_literals

from tests import with_settings
from tests.web.splinter import TestCase, logged_in
from catsnap import Client
from catsnap.table.image import Image
from nose.tools import eq_


class TestImageEdit(TestCase):
    @logged_in
    @with_settings(bucket='frootypoo')
    def test_click_on_the_title(self):
        session = Client().session()
        image = Image(filename='asdf', title='click on this!')
        session.add(image)
        session.flush()
        self.browser.visit('http://localhost:65432/image/%d' % image.image_id)
        assert self.browser.is_text_present('click on this!'), \
            "Didn't find expected title"

        title = self.browser.find_by_css('h2').first
        title.click()
        title_edit_field = self.browser.find_by_css('header input')
        assert title_edit_field, "Didn't find a title-edit field!"
        eq_(title_edit_field.value, 'click on this!')
