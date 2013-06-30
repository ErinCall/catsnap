from __future__ import unicode_literals

from tests import with_settings
from tests.web.splinter import TestCase, logged_in
from catsnap import Client
from catsnap.table.image import Image
from nose.tools import eq_


class TestImageEdit(TestCase):
    @logged_in
    @with_settings(bucket='frootypoo')
    def test_edit_the_title(self):
        session = Client().session()
        image = Image(filename='asdf', title='click on this!')
        session.add(image)
        session.flush()
        self.visit_url('/image/%d' % image.image_id)
        assert self.browser.is_text_present('click on this!'), \
            "Didn't find expected title"

        title = self.browser.find_by_css('h2').first
        assert title, "Didn't find a title"
        title.click()
        title_edit_field = self.browser.find_by_css('header input')
        assert title_edit_field, "Didn't find a title-edit field!"
        eq_(title_edit_field.value, 'click on this!')
        title_edit_field.fill('I clicked\n')

        title = self.browser.find_by_css('h2').first
        assert title, "Didn't find a title after first edit"
        title.click()
        title_edit_field = self.browser.find_by_css('header input')
        assert title_edit_field, "didn't find a title-edit field after first edit"
        eq_(title_edit_field.value, 'I clicked')
        title_edit_field.fill("I clicked TWICE\n")

        image = session.query(Image).\
                filter(Image.image_id == image.image_id).\
                one()
        eq_(image.title, 'I clicked TWICE')

    @logged_in
    @with_settings(bucket='frootypoo')
    def test_edit_the_description(self):
        session = Client().session()
        image = Image(filename='deafbeef')
        session.add(image)
        session.flush()
        self.visit_url('/image/%d' % image.image_id)
        assert self.browser.is_text_present('(click to add description)'), \
            "Didn't find description placeholder"

        description = self.browser.find_by_css('#description span')
        assert description, "Didn't find description"
        description.click()
        description_edit = self.browser.find_by_css('#description textarea')
        assert description_edit, "Didn't find a description-edit field!"
        eq_(description_edit.value, '(click to add description)')
        description_edit.fill("this image fills me with glee\t")

        description = self.browser.find_by_css('#description span')
        assert description, "Didn't find description after editing"
        description.click()
        description_edit = self.browser.find_by_css('#description textarea')
        assert description_edit, "Didn't find a description-edit field after editing"
        eq_(description_edit.value, 'this image fills me with glee')
        description_edit.fill("this image makes me sad\t")

        image = session.query(Image).\
                filter(Image.image_id == image.image_id).\
                one()
        eq_(image.description, 'this image makes me sad')
