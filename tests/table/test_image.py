from __future__ import unicode_literals

import time
from tests import TestCase
from catsnap import Client
from nose.tools import eq_
from mock import patch

from catsnap.table.album import Album
from catsnap.table.image import Image, ImageResize, ImageContents
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

    @patch('catsnap.table.created_at_bookkeeper.time')
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

    def test_neighbors_is_nones_when_the_image_has_no_album(self):
        image = Image(filename='faceface')
        eq_((None, None), image.neighbors())

    def test_neighbors_is_none_and_one_when_there_is_a_greater_neighbor(self):
        session = Client().session()
        album = Album(name='Light me up')
        session.add(album)
        session.flush()

        image = Image(filename='f1acc1d', album_id=album.album_id)
        session.add(image)
        next = Image(filename='1ace', album_id=album.album_id)
        session.add(next)
        session.flush()

        eq_((None, next), image.neighbors())

    def test_neighbors_is_one_and_none_when_the_image_has_a_lesser_neighbor(self):
        session = Client().session()
        album = Album(name='Light me up')
        session.add(album)
        session.flush()

        prev = Image(filename='1ace', album_id=album.album_id)
        session.add(prev)
        image = Image(filename='f1acc1d', album_id=album.album_id)
        session.add(image)
        session.flush()

        eq_((prev, None), image.neighbors())

    def test_neighbors_is_both_neighbors_when_many_neighbors_are_present(self):
        session = Client().session()
        album = Album(name='Light me up')

        session.add(album)
        session.flush()

        session.add(Image(filename='babeface'))
        session.add(Image(filename='cafebabe', album_id=album.album_id))
        prev = Image(filename='1ace', album_id=album.album_id)
        session.add(prev)
        image = Image(filename='f1acc1d', album_id=album.album_id)
        session.add(image)
        next = Image(filename='bab1e5', album_id=album.album_id)
        session.add(next)
        session.add(Image(filename='acebabe', album_id=album.album_id))
        session.flush()

        eq_((prev, next), image.neighbors())

    def test_neighbors_skips_over_images_from_other_albums(self):
        session = Client().session()
        hobbiton = Album(name='Hobbiton')
        session.add(hobbiton)
        hardbottle = Album(name='Hardbottle')
        session.add(hardbottle)
        session.flush()

        samwise = Image(filename='5411111115e', album_id=hobbiton.album_id)
        session.add(samwise)
        bilbo = Image(filename='b11b0', album_id=hobbiton.album_id)
        session.add(bilbo)
        lobelia = Image(filename='10be11a', album_id=hardbottle.album_id)
        session.add(lobelia)
        frodo = Image(filename='f0d0', album_id=hobbiton.album_id)
        session.add(frodo)
        session.flush()

        eq_((samwise, frodo), bilbo.neighbors())

    def test_image_resizes_do_upserts(self):
        session = Client().session()
        image = Image(filename='ac1d1c')
        session.add(image)
        session.flush()

        resize = ImageResize(
            image_id=image.image_id,
            width=15,
            height=15,
            suffix="little")
        session.add(resize)
        session.flush()

        resize = ImageResize(
            image_id=image.image_id,
            width=15,
            height=15,
            suffix="small")
        session.add(resize)
        session.flush()

        resize = session.query(ImageResize).\
            filter(ImageResize.image_id == image.image_id).\
            one()
        eq_('small', resize.suffix)

class TestImageContents(TestCase):
    @patch('catsnap.table.created_at_bookkeeper.time')
    def test_created_at_is_set_on_creation(self, mock_time):
        now = time.strptime('2011-05-09 13:01:01', '%Y-%m-%d %H:%M:%S')
        mock_time.strftime = time.strftime
        mock_time.gmtime.return_value = now
        session = Client().session()
        image = Image(filename='face')
        session.add(image)
        session.flush()
        image_contents = ImageContents(image_id=image.image_id,
                                       contents=b'hootybooty')
        eq_(image_contents.created_at, time.strftime('%Y-%m-%d %H:%M:%S', now))
