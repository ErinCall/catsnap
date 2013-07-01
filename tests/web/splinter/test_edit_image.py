from __future__ import unicode_literals

from tests import with_settings
from tests.web.splinter import TestCase, logged_in
from catsnap import Client
from catsnap.table.image import Image
from catsnap.table.image_tag import ImageTag
from catsnap.table.tag import Tag
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

    @logged_in
    @with_settings(bucket='whooyeah')
    def test_add_and_remove_a_tag(self):
        session = Client().session()
        image = Image(filename='bab1e5')
        session.add(image)
        session.flush()
        self.visit_url('/image/%d' % image.image_id)
        assert self.browser.is_text_present('(click to add a tag)'),\
            "Didn't find tag-adder"
        add_tag = self.browser.find_by_css('#add-tag')
        add_tag.click()
        tag_name = self.browser.find_by_css('li input')
        tag_name.fill("booya\n")

        new_tag = self.browser.find_by_css('li span').first
        eq_(new_tag.text, 'booya')

        assert self.browser.is_text_present('(click to add a tag)'),\
            "Didn't find new tag-adder"

        image_tag = session.query(ImageTag).\
                join(Tag, Tag.tag_id == ImageTag.tag_id).\
                filter(Tag.name == 'booya').\
                one()
        eq_(image_tag.image_id, image.image_id)

        self.browser.find_link_by_text('x').first.click()

        assert not self.browser.is_text_present('booya'), \
            "Tag wasn't deleted from the page"

        image_tags = session.query(ImageTag).all()
        eq_(image_tags, [])
