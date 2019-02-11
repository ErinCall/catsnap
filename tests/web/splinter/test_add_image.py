from __future__ import unicode_literals

from selenium.webdriver.common.keys import Keys
from tests import with_settings
from tests.image_helper import SOME_GIF, SOME_PNG
from tests.web.splinter import TestCase, logged_in
from catsnap import Client
from catsnap.table.image import Image
from catsnap.table.album import Album
from catsnap.table.image_tag import ImageTag
from catsnap.table.tag import Tag
from mock import patch, Mock
from nose.tools import eq_, nottest

import time

class UploadTestCase(TestCase):
    @nottest
    @patch('catsnap.web.controllers.image.ImageTruck')
    def upload_one_image(self, ImageTruck):
        ImageTruck.new_from_stream.return_value = self.mock_truck()

        self.visit_url('/add')
        self.browser.attach_file('file[]', SOME_GIF)
        self.browser.find_by_css('input[name="file-submit"]').click()

    @nottest
    def mock_truck(self):
        truck = Mock()
        with open(SOME_GIF, 'r') as fh:
            truck.contents = fh.read()
        truck.url.return_value = 'https://catsnap.cdn/ca7face'
        truck.filename = 'ca7face'
        truck.content_type = 'image/gif'
        return truck


class TestUploadImage(UploadTestCase):
    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_try_to_add_a_bad_url(self):
        self.visit_url('/add')
        self.browser.click_link_by_text('From Url')
        url_field = self.browser.find_by_css('input[name="url"]')
        assert url_field, "Didn't find the url input"
        url_field.fill('http://example.com/images/example_image_4.jpg')
        self.browser.find_by_css('input[name="url-submit"]').click()

        assert self.browser.is_text_present('That url is no good'), \
            "Didn't see a user-facing error message!"

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_errors_clear_previous_errors(self):
        self.visit_url('/add')
        self.browser.click_link_by_text('From Url')

        submit_button = self.browser.find_by_css('input[name="url-submit"]')
        submit_button.click()
        assert self.browser.is_text_present(
                'Please submit either a file or a url.'), \
            "Didn't see a user-facing error message!"

        url_field = self.browser.find_by_css('input[name="url"]')
        assert url_field, "Didn't find the url input"
        url_field.fill('SOMETHING INVALID')
        submit_button.click()

        assert self.browser.is_text_present('That url is no good'), \
            "Didn't see a user-facing error message!"
        assert not self.browser.is_text_present('submit either a file'), \
            "The old error wasn't cleared!"

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_successes_clear_previous_errors(self, ImageTruck):
        ImageTruck.new_from_url.return_value = self.mock_truck()
        self.visit_url('/add')
        self.browser.click_link_by_text('From Url')

        submit_button = self.browser.find_by_css('input[name="url-submit"]')
        submit_button.click()
        assert self.browser.is_text_present(
                'Please submit either a file or a url.'), \
            "Didn't see a user-facing error message!"

        url_field = self.browser.find_by_css('input[name="url"]')
        assert url_field, "Didn't find the url input"
        url_field.fill('http://cdn.mlkshk.com/r/110WR')
        submit_button.click()

        assert not self.browser.is_text_present('submit either a file'), \
            "The old error wasn't cleared!"

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_add_by_url(self, ImageTruck):
        ImageTruck.new_from_url.return_value = self.mock_truck()

        self.visit_url('/add')
        self.browser.click_link_by_text('From Url')

        url_field = self.browser.find_by_css('input[name="url"]')
        assert url_field, "Didn't find the url input"
        assert url_field.first.visible, "The url input isn't visible"
        url_field.fill('http://cdn.mlkshk.com/r/111DS')
        self.browser.find_by_css('input[name="url-submit"]').click()

        img = self.browser.find_by_css('img')[0]
        eq_(img['src'], 'http://localhost:65432/public/img/large-throbber.gif')

        url_field = self.browser.find_by_css('input[name="url"]')
        assert url_field, "The page didn't create a new url input"
        assert url_field.first.visible, "The new url input isn't visible"

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_add_by_file(self):
        self.visit_url('/add')

        file_field = self.browser.find_by_css('input[type="file"]').first
        file_label = self.browser.find_by_css('label[for="file"]').first
        assert file_field, "Didn't find the file input"
        assert not file_field.visible, "The file input is visible"
        assert file_label, "Didn't find a label for the file input"
        assert file_label.visible, "The file label isn't visible"

        self.browser.attach_file('file[]', SOME_GIF)
        self.browser.find_by_css('input[name="file-submit"]').click()

        img = self.browser.find_by_css('img')[0]
        eq_(img['src'], 'http://localhost:65432/public/img/large-throbber.gif')

        file_field = self.browser.find_by_css('input[type="file"]')
        file_label = self.browser.find_by_css('label[for="file"]')
        assert file_field, "The page didn't create a new upload form"

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_file_labels_track_the_input_value(self):
        self.visit_url('/add')

        file_field = self.browser.find_by_css('input[type="file"]').first
        file_label = self.browser.find_by_css('label[for="file"]').first
        assert file_field, "Didn't find the file input"
        assert file_label, "Didn't find a label for the file input"

        self.browser.attach_file('file[]', SOME_PNG)

        eq_(file_label.text, 'C:\\fakepath\\test_image_592x821.png')

class TestAlbumFunctions(UploadTestCase):
    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_upload_to_an_album(self, ImageTruck):
        ImageTruck.new_from_url.return_value = self.mock_truck()
        session = Client().session()
        album = Album(name='fotoz')
        session.add(album)
        session.flush()

        self.visit_url('/add')
        album_select = self.browser.find_by_name('album')
        album_select.select(str(album.album_id))

        self.browser.click_link_by_text('From Url')
        url_field = self.browser.find_by_css('input[name="url"]')
        url_field.fill('http://cdn.mlkshk.com/r/111V1')
        self.browser.find_by_css('input[name="url-submit"]').click()

        # force a wait for the upload response
        self.browser.find_by_css('textarea')

        image = session.query(Image).one()
        eq_(image.album_id, album.album_id)

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_create_new_album(self):
        self.visit_url('/add')

        self.browser.click_link_by_partial_text('create new album')
        album_input = self.browser.find_by_name('album-name').first
        album_input.type('Soviet Kitsch')
        album_input.type(Keys.ENTER)

        album_select = self.browser.find_by_name('album').first

        album = Client().session().query(Album).one()
        eq_(album.name, "Soviet Kitsch")

        options = album_select.find_by_tag('option')
        soviet_kitsch = filter(lambda o: o.value == unicode(album.album_id),
                               options)[0]
        assert soviet_kitsch, "The new album wasn't added to the dropdown!"
        assert soviet_kitsch.selected, "The new album wasn't selected!"
        assert not self.browser.find_by_css('#new-album').first.visible, \
            "The modal didn't hide correctly!"

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_invalid_album_names_get_an_error_message(self):
        session = Client().session()
        session.add(Album(name="Begin To Hope"))
        session.flush()

        self.visit_url('/add')

        self.browser.click_link_by_partial_text('create new album')
        album_input = self.browser.find_by_name('album-name').first
        album_input.type('Begin To Hope')
        album_input.type(Keys.ENTER)

        assert self.browser.find_by_css('#new-album').first.visible, \
            "The modal was hidden when there was an error!"
        assert self.browser.is_text_present(
            'There is already an album with that name.'), \
            "The album-name error message wasn't displayed!"

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_album_name_input_is_cleared_on_submit(self):
        self.visit_url('/add')

        self.browser.click_link_by_partial_text('create new album')
        album_input = self.browser.find_by_name('album-name').first
        album_input.type('Soviet Kitsch')
        album_input.type(Keys.ENTER)

        self.browser.click_link_by_partial_text('create new album')
        album_input = self.browser.find_by_name('album-name').first
        eq_(album_input.value, '')

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_previous_errors_are_cleared_on_success(self):
        session = Client().session()
        session.add(Album(name="Led Zeppelin"))
        session.flush()

        self.visit_url('/add')

        self.browser.click_link_by_partial_text('create new album')
        album_input = self.browser.find_by_name('album-name').first
        album_input.type('Led Zeppelin')
        album_input.type(Keys.ENTER)

        assert self.browser.is_text_present(
            'There is already an album with that name.'), \
            "The album-name error message wasn't displayed!"
        album_input.type('Led Zeppelin II')
        album_input.type(Keys.ENTER)

        self.browser.click_link_by_partial_text('create new album')
        assert not self.browser.is_text_present(
            'There is already an album with that name.'), \
            "The album-name error message overstayed its welcome!"


class TestAddTagsAfterUpload(UploadTestCase):
    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_tab_from_tag_input_focuses_next_tag_input_and_saves(self):
        self.upload_one_image()
        self.browser.click_link_by_text('Add tag')
        tag_input = self.browser.find_by_name('tag').first
        tag_input.type('chipmunk')
        tag_input.type(Keys.TAB)
        time.sleep(0.01)
        # there is no .is_focused or anything, so we'll do it inside-out:
        # look for a focused input and assert that it's the right one.
        next_tag = self.browser.find_by_css('input:focus').first
        eq_(next_tag['name'], "tag", "wrong input was focused")

        session = Client().session()
        image = session.query(Image).one()
        eq_(list(image.get_tags()), ["chipmunk"])

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_escape_from_tag_input_cancels_tag_editing(self):
        self.upload_one_image()
        self.browser.click_link_by_text('Add tag')
        tag_input = self.browser.find_by_name('tag').first
        tag_input.type('flerp')
        tag_input.type(Keys.ESCAPE)

        assert self.browser.is_element_not_present_by_name('tag'), \
            "the tag-name input wasn't cleared!"
        assert self.browser.find_link_by_text('Add tag').first, \
            "The add-tag link wasn't put back in!"

        tags = Client().session().query(ImageTag).all()
        eq_(tags, [])

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_empty_tags_are_not_saved(self):
        self.upload_one_image()
        self.browser.click_link_by_text('Add tag')
        tag_input = self.browser.find_by_name('tag').first
        tag_input.type(' ')
        tag_input.type(Keys.ENTER)

        assert self.browser.is_element_not_present_by_name('tag'), \
            "the tag-name input wasn't cleared!"
        assert self.browser.find_link_by_text('Add tag').first, \
            "The add-tag link wasn't put back in!"

        tags = Client().session().query(ImageTag).all()
        eq_(tags, [])

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_remove_tag(self):
        self.upload_one_image()
        self.browser.click_link_by_text('Add tag')
        tag_input = self.browser.find_by_name('tag').first
        tag_input.type('intens')
        tag_input.type(Keys.ENTER)
        time.sleep(0.01)

        tags = Client().session().query(Tag.name).all()
        eq_(tags, [('intens',)])
        image_tags = Client().session().query(ImageTag).all()
        eq_(len(image_tags), 1)

        self.browser.click_link_by_text('intens')

        image_tags = Client().session().query(ImageTag).all()
        eq_(image_tags, [])

class TestEditAttributes(UploadTestCase):
    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_submit_title(self):
        self.upload_one_image()
        title_input = self.browser.find_by_name('title').first
        title_input.type('Tiny chipmunk dancing')
        title_input.type(Keys.ENTER)
        time.sleep(0.01)

        image = Client().session().query(Image).one()
        eq_(image.title, "Tiny chipmunk dancing")

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_submit_description(self):
        self.upload_one_image()
        description_input = self.browser.find_by_name('description').first
        description_input.fill('A chipmunk dances.\nIt dances its heart out')
        self.browser.find_by_name('save').click()

        image = Client().session().query(Image).one()
        eq_(image.description, "A chipmunk dances.\nIt dances its heart out")

    @logged_in
    @with_settings(aws={'bucket': 'frootypoo'})
    def test_blurring_inputs_submits_changes(self):
        self.upload_one_image()
        description_input = self.browser.find_by_name('description').first
        description_input.fill('A chipmunk dances.\nIt dances its heart out')
        title_input = self.browser.find_by_name('title').first
        title_input.fill('Tiny chipmunk dancing')

        self.browser.click_link_by_text('From File')

        image = Client().session().query(Image).one()
        eq_(image.title, "Tiny chipmunk dancing")
        eq_(image.description, "A chipmunk dances.\nIt dances its heart out")
