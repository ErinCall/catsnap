from __future__ import unicode_literals

from tests import TestCase
from catsnap import Client
from nose.tools import eq_

from catsnap.table.image import Image
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
