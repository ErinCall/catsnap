from __future__ import unicode_literals

import time
from tests import TestCase
from catsnap import Client
from nose.tools import eq_
from mock import patch

from catsnap.table.image import Image
from catsnap.table.album import Album
from catsnap.table.tag import Tag
from catsnap.table.image_tag import ImageTag

class TestImages(TestCase):
    def test_add_tags_adds_image_tag_rows(self):
        session = Client().session()
        tag = Tag(name='booya')
        session.add(tag)
        image = Image(filename='baba15')
        session.add(image)
        image.add_tags(['booya'])

        image_tag = session.query(ImageTag).\
                filter(ImageTag.image_id == image.image_id).\
                filter(ImageTag.tag_id == tag.tag_id).\
                first()

        assert image_tag, 'no image/tag mapping was created'

    def test_add_tags_creates_tag_row_if_necessary(self):
        session = Client().session()
        image = Image(filename='baba15')
        session.add(image)
        image.add_tags(['booya'])

        tag = session.query(Tag).\
                filter(Tag.name=='booya').\
                first()

        assert tag, 'no tag was created'

    def test_remove_tag(self):
        session = Client().session()
        tag = Tag(name='booya')
        image = Image(filename='bab1e5')
        session.add(tag)
        session.add(image)
        session.flush()
        image_tag = ImageTag(image_id=image.image_id, tag_id=tag.tag_id)
        session.add(image_tag)
        session.flush()

        image.remove_tag('booya')

        image_tags = session.query(ImageTag).all()
        eq_(image_tags, [])

    def test_creating_with_a_new_source_url_updates_existing_record(self):
        session = Client().session()
        session.add(Image(filename='badcafe', source_url='example.com'))
        session.flush()
        session.add(Image(filename='badcafe', source_url='examp.le'))
        session.flush()

        source_url = session.query(Image.source_url).first()
        eq_(source_url, ('examp.le',))

    def test_get_tags(self):
        session = Client().session()
        image = Image(filename='cafebabe')
        mustache = Tag(name='mustache')
        gif = Tag(name='gif')
        session.add(image)
        session.add(mustache)
        session.add(gif)
        session.flush()
        session.add(ImageTag(tag_id=mustache.tag_id, image_id=image.image_id))
        session.add(ImageTag(tag_id=gif.tag_id, image_id=image.image_id))
        session.flush()

        tags = image.get_tags()
        eq_(list(tags), ['mustache', 'gif'])

    @patch('catsnap.table.image.time')
    def test_created_at_is_set_on_creation(self, mock_time):
        now = time.strptime('2011-05-09 13:01:01', '%Y-%m-%d %H:%M:%S')
        mock_time.strftime = time.strftime
        mock_time.gmtime.return_value = now
        session = Client().session()
        image = Image(filename='face')
        eq_(image.created_at, time.strftime('%Y-%m-%d %H:%M:%S', now))

    def test_find_by_filename(self):
        session = Client().session()
        session.add(Image(filename='deadbeef', source_url='example.com/foo'))
        session.flush()

        image = Image.find_by_filename('deadbeef')
        eq_(image.source_url, 'example.com/foo')

    def test_find_by_filename__is_case_insensitive(self):
        session = Client().session()
        session.add(Image(filename='deadbeef', source_url='example.com/foo'))
        session.flush()

        image = Image.find_by_filename('DEADBEEF')
        eq_(image.source_url, 'example.com/foo')

    def test_caption__defaults_to_title(self):
        session = Client().session()
        image = Image(title='the title', filename='')
        session.add(image)
        image.add_tags(['cat', 'awesome'])

        eq_(image.caption(), 'the title')

    def test_caption__falls_back_to_tags(self):
        session = Client().session()
        image = Image(title='', filename='')
        session.add(image)
        image.add_tags(['cat', 'awesome'])

        eq_(image.caption(), 'awesome cat')

    def test_caption__falls_back_to_filename(self):
        image = Image(title='', filename='the filename')

        eq_(image.caption(), 'the filename')

    def test_previous_image_id_is_none_if_no_album(self):
        image = Image(filename='the filename')

        eq_(image.previous_image_id(), None)

    def test_previous_image_id__finds_previous_in_album(self):
        session = Client().session()
        album = Album(name='my pictures')
        session.add(album)
        session.flush()

        first = Image(
            album_id=album.album_id, filename='first', created_at='20070514')
        second = Image(
            album_id=album.album_id, filename='second', created_at='20100509')
        third = Image(
            album_id=album.album_id, filename='third', created_at='20130804')
        session.add(first)
        session.add(second)
        session.add(third)
        session.flush()

        eq_(third.previous_image_id(), second.image_id)
        eq_(second.previous_image_id(), first.image_id)
        eq_(first.previous_image_id(), None)

    def test_next_image_id_is_none_if_no_album(self):
        image = Image(filename='the filename')

        eq_(image.next_image_id(), None)

    def test_next_image_id__finds_next_in_album(self):
        session = Client().session()
        album = Album(name='my pictures')
        session.add(album)
        session.flush()

        first = Image(
            album_id=album.album_id, filename='first', created_at='20070514')
        second = Image(
            album_id=album.album_id, filename='second', created_at='20100509')
        third = Image(
            album_id=album.album_id, filename='third', created_at='20130804')
        session.add(first)
        session.add(second)
        session.add(third)
        session.flush()

        eq_(first.next_image_id(), second.image_id)
        eq_(second.next_image_id(), third.image_id)
        eq_(third.next_image_id(), None)
