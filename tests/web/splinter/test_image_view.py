from __future__ import unicode_literals

from tests import with_settings
from tests.web.splinter import TestCase, logged_in
from selenium.webdriver.common.keys import Keys
from catsnap import Client
from catsnap.table.image import Image
from catsnap.table.album import Album
from nose.tools import eq_

import time

class TestImageView(TestCase):
    @with_settings(aws={'bucket': 'humptydump'})
    def test_view_an_image(self):
        session = Client().session()

        album = Album(name="tophos")
        session.add(album)
        session.flush()

        silly = Image(album_id=album.album_id, filename="silly")
        session.add(silly)
        session.flush()

        self.visit_url('/image/{0}'.format(silly.image_id))

        images = self.browser.find_by_tag('img')
        eq_(map(lambda i: i['src'], images), [
            'https://s3.amazonaws.com/humptydump/silly',
        ])
        eq_(map(lambda i: i['alt'], images), ['silly'])

        assert self.browser.is_text_present('silly')

        edit_button = self.browser.find_by_id('edit')
        assert not edit_button, "Edit button visible to logged-out user!"
        title_field = self.browser.find_by_css('input[name="title"]')
        assert not title_field.visible, "Edit controls visible to logged-out user!"

class TestEditImage(TestCase):
    @logged_in
    @with_settings(aws={'bucket': 'humptydump'})
    def test_edit_title(self):
        session = Client().session()

        silly = Image(filename="silly", title="Silly Picture")
        session.add(silly)
        session.flush()

        self.visit_url('/image/{0}'.format(silly.image_id))

        self.browser.click_link_by_text('Edit')

        caption = self.browser.find_by_id('caption')
        assert not caption.visible, "Caption header didn't disappear!"
        title_field = self.browser.find_by_css('input[name="title"]')
        assert title_field.visible, "No title-edit field!"
        eq_(title_field.value, 'Silly Picture')

        title_field.clear()
        title_field.type('Goofy Picture')
        title_field.type(Keys.ENTER)

        self.browser.click_link_by_text('Stop Editing')
        assert not title_field.visible, "Title field didn't go away!"

        eq_(caption.text, 'Goofy Picture')

        eq_(self.browser.title, 'Goofy Picture - Catsnap')

        session.refresh(silly)
        eq_(silly.title, 'Goofy Picture')

    @logged_in
    @with_settings(aws={'bucket': 'humptydump'})
    def test_stop_editing_submits(self):
        session = Client().session()

        silly = Image(filename="silly", title="Silly Picture")
        session.add(silly)
        session.flush()

        self.visit_url('/image/{0}'.format(silly.image_id))

        self.browser.click_link_by_text('Edit')

        title_field = self.browser.find_by_css('input[name="title"]')
        assert title_field.visible, "No title-edit field!"

        title_field.fill('Goofy Picture')

        self.browser.click_link_by_text('Stop Editing')

        session.refresh(silly)
        eq_(silly.title, 'Goofy Picture')

    @logged_in
    @with_settings(aws={'bucket': 'humptydump'})
    def test_edit_description(self):
        session = Client().session()

        silly = Image(filename="silly", title="Silly Picture")
        session.add(silly)
        session.flush()

        self.visit_url('/image/{0}'.format(silly.image_id))
        self.browser.click_link_by_text('Edit')

        description_field = self.browser.find_by_id('description')
        assert description_field.visible, "No description-edit field!"

        description_field.fill('This is silly to do.\nWhy is it done?')

        self.browser.click_link_by_text('Stop Editing')

        session.refresh(silly)
        eq_(silly.description, 'This is silly to do.\nWhy is it done?')

        description_paras = self.browser.find_by_css('p.image-description')
        eq_([p.text for p in description_paras], [
            'This is silly to do.',
            'Why is it done?'
        ])

    @logged_in
    @with_settings(aws={'bucket': 'humptydump'})
    def test_edit_tags(self):
        session = Client().session()

        pic = Image(filename="silly", title="Silly Picture")
        session.add(pic)
        session.flush()

        pic.add_tags(['goofy', 'silly'])
        session.flush()

        self.visit_url('/image/{0}'.format(pic.image_id))

        tag_button = self.browser.find_by_id('tag-button')
        assert tag_button, "Couldn't find a button for listing tags!"
        tag_button.click()

        tags = self.browser.find_by_css('li.tag')
        assert all([t.visible for t in tags]), "Tag listing was not visible!"
        eq_([t.text for t in tags], ['goofy', 'silly'])

        self.browser.click_link_by_text('Edit')

        assert all([not t.visible for t in tags]), "Tag listing didn't disappear!"

        tag_removes = self.browser.find_by_css('a.remove-tag')
        eq_([t.text for t in tag_removes], ['goofy', 'silly'])
        assert all([t.visible for t in tag_removes]), "Remove tag controls weren't visible!"

        add_tag = self.browser.find_by_css('a.add-tag')
        eq_(add_tag.text, 'Add tag')
        assert add_tag.visible, "Add tag control wasn't visible!"

        tag_removes[0].click()

        eq_(list(pic.get_tags()), ['silly'])
        tag_removes = self.browser.find_by_css('a.remove-tag')
        eq_([t.text for t in tag_removes], ['silly'])

        self.browser.click_link_by_text('Stop Editing')
        tag_button.click()
        tags = self.browser.find_by_css('li.tag')
        assert all([t.visible for t in tags]), "Tag listing was not visible!"
        eq_([t.text for t in tags], ['silly'])
        self.browser.click_link_by_text('Edit')

        add_tag.click()
        focused_input = self.browser.find_by_css('input:focus').first
        tag_input = self.browser.find_by_id('tag').first
        eq_(focused_input['id'], 'tag', "Add-tag input wasn't automatically focused!")
        tag_input.type('funny')
        tag_input.type(Keys.ENTER)

        time.sleep(0.01)
        tag_removes = self.browser.find_by_css('a.remove-tag')
        eq_([t.text for t in tag_removes], ['silly', 'funny'])

        eq_(list(pic.get_tags()), ['silly', 'funny'])

        self.browser.click_link_by_text('Stop Editing')
        tag_button.click()
        tags = self.browser.find_by_css('li.tag')
        assert all([t.visible for t in tags]), "Tag listing was not visible!"
        eq_([t.text for t in tags], ['silly', 'funny'])
        self.browser.click_link_by_text('Edit')


        tag_removes[1].click()
        eq_(list(pic.get_tags()), ['silly'])

    @logged_in
    @with_settings(aws={'bucket': 'humptydump'})
    def test_add_tag_to_an_untagged_image(self):
        session = Client().session()
        pic = Image(filename="tagless", title="Untagged Picture")
        session.add(pic)
        session.flush()

        self.visit_url('/image/{0}'.format(pic.image_id))

        tag_button = self.browser.find_by_id('tag-button')
        assert tag_button, "Couldn't find a button for listing tags!"
        assert tag_button.has_class("disabled"), \
            "Tag button enabled without tags!"

        self.browser.click_link_by_text('Edit')
        add_tag = self.browser.find_by_css('a.add-tag')
        add_tag.click()
        tag_input = self.browser.find_by_id('tag')[0]
        tag_input.type('untagged')
        tag_input.type(Keys.ENTER)

        self.browser.click_link_by_text('Stop Editing')
        tag_button.click()
        tags = self.browser.find_by_css('li.tag')
        assert all([t.visible for t in tags]), "Tag listing was not visible!"
        eq_([t.text for t in tags], ['untagged'])


    @logged_in
    @with_settings(aws={'bucket': 'humptydump'})
    def test_remove_last_tag(self):
        session = Client().session()
        pic = Image(filename="tagged", title="Untagged Picture")
        session.add(pic)
        session.flush()

        pic.add_tags(['one'])
        session.flush()

        self.visit_url('/image/{0}'.format(pic.image_id))

        self.browser.click_link_by_text('Edit')
        remove_tag = self.browser.find_by_css('a.remove-tag')
        remove_tag.click()

        self.browser.click_link_by_text('Stop Editing')
        tag_button = self.browser.find_by_id('tag-button')
        assert tag_button.has_class("disabled"), \
            "Tag button enabled without tags!"

    @logged_in
    @with_settings(aws={'bucket': 'humptydump'})
    def test_tabbing_out_of_tab_input_opens_and_focuses_a_new_one(self):
        session = Client().session()
        pic = Image(filename="acebabe")
        session.add(pic)
        session.flush()

        self.visit_url('/image/{0}'.format(pic.image_id))

        self.browser.click_link_by_text('Edit')
        add_tag = self.browser.find_by_css('a.add-tag')
        add_tag.click()
        tag_input = self.browser.find_by_id('tag')[0]
        tag_input.type('babe')
        tag_input.type(Keys.TAB)
        tag_removes = self.browser.find_by_css('a.remove-tag')
        eq_([t.text for t in tag_removes], ['babe'])

        focused_input = self.browser.find_by_css('input:focus').first
        eq_(focused_input['id'], 'tag')

        eq_(list(pic.get_tags()), ['babe'])

    @logged_in
    @with_settings(aws={'bucket': 'humptydump'})
    def test_hitting_escape_aborts_editing_without_saving(self):
        session = Client().session()
        pic = Image(filename="acebabe")
        session.add(pic)
        session.flush()

        self.visit_url('/image/{0}'.format(pic.image_id))

        self.browser.click_link_by_text('Edit')
        add_tag = self.browser.find_by_css('a.add-tag')
        add_tag.click()
        tag_input = self.browser.find_by_id('tag')[0]
        tag_input.type('babe')
        tag_input.type(Keys.ESCAPE)

        add_tag = self.browser.find_by_css('a.add-tag')
        assert add_tag.visible, "Editing didn't abort!"

        eq_(list(pic.get_tags()), [])

    @logged_in
    @with_settings(aws={'bucket': 'humptydump'})
    def test_edit_album(self):
        session = Client().session()
        pix = Album(name="pix")
        highlights = Album(name="highlights")
        session.add(pix)
        session.add(highlights)
        session.flush()

        pic = Image(filename="acebabe", album_id=pix.album_id)
        session.add(pic)
        session.flush()

        self.visit_url('/image/{0}'.format(pic.image_id))

        self.browser.click_link_by_text('Edit')

        album_dropdown = self.browser.find_by_css('select.edit-album')
        assert album_dropdown.visible, "Album select wasn't visible!"
        album_options = album_dropdown.find_by_css('option')

        eq_(album_options[1]['selected'], 'true')

        album_dropdown.select(str(highlights.album_id))
        self.browser.click_link_by_text('Stop Editing')

        session.refresh(pic)
        eq_(int(pic.album_id), highlights.album_id)
