from __future__ import unicode_literals

import json
from tests import TestCase, with_settings, logged_in
from nose.tools import eq_
from catsnap import Client
from catsnap.table.image import Image
from catsnap.table.tag import Tag
from catsnap.table.image_tag import ImageTag
from catsnap.table.album import Album

from unittest.case import SkipTest

class TestUpdateImage(TestCase):
    @logged_in
    @with_settings(bucket='snapcats')
    def test_update_an_image(self):
        session = Client().session()
        album = Album(name='cow shots')
        session.add(album)
        image = Image(filename='deadbeef',
                      description='one time I saw a dead cow',
                      title='dead beef')

        session.add(image)
        session.flush()

        response = self.app.patch('/image/%d.json' % image.image_id, data={
            'attributes': json.dumps({
                'album_id': str(album.album_id),
            })
        })
        body = json.loads(response.data)
        eq_(body['status'], 'ok')

        del image
        image = session.query(Image).one()
        eq_(image.album_id, album.album_id)

    @logged_in
    def test_unknown_attributes_generate_an_error(self):
        session = Client().session()
        image = Image(filename='deadbeef')
        session.add(image)
        session.flush()

        response = self.app.patch('/image/%d.json' % image.image_id, data={
            'attributes': json.dumps({
                'rochambeau': 'fleur de lis',
            })
        })
        body = json.loads(response.data)
        eq_(body['status'], 'error')
        eq_(body['error_description'], "No such attribute 'rochambeau'")

    @logged_in
    def test_invalid_album_id_generates_an_error(self):
        session = Client().session()
        image = Image(filename='deadbeef')
        session.add(image)
        session.flush()

        response = self.app.patch('/image/%d.json' % image.image_id, data={
            'attributes': json.dumps({
                'album_id': 5,
            })
        })

        body = json.loads(response.data)
        eq_(body['status'], 'error')
        eq_(body['error_description'], "No such album_id '5'")

    @logged_in
    def test_clear_album_id(self):
        session = Client().session()
        album = Album(name='wolves')
        session.add(album)
        session.flush()
        image = Image(filename='01f5', album_id=album.album_id)
        session.add(image)
        session.flush()

        response = self.app.patch('/image/%d.json' % image.image_id, data={
            'attributes': json.dumps({
                'album_id': '',
            })
        })

        body = json.loads(response.data)
        eq_(body['status'], 'ok')

        image = session.query(Image).one()
        eq_(image.album_id, None)

    def test_login_is_required(self):
        response = self.app.patch('/image/1.json', data={
            'attributes': json.dumps({
                'title': 'BUTTFARTS',
            }),
        })
        eq_(response.status_code, 401)

    @logged_in
    def test_add_a_tag(self):
        session = Client().session()
        image = Image(filename='deadbeef')
        session.add(image)
        session.flush()

        response = self.app.patch('/image/%d.json' % image.image_id, data={
            'add_tag': 'cow',
        })
        eq_(response.status_code, 200)

        body = json.loads(response.data)
        eq_(body['status'], 'ok')

        tag = session.query(Tag).filter(Tag.name == 'cow').one()
        image_tag = session.query(ImageTag).\
                filter(ImageTag.tag_id == tag.tag_id).\
                one()
        eq_(image_tag.image_id, image.image_id)

    @logged_in
    def test_remove_a_tag(self):
        session = Client().session()
        image = Image(filename='deadbeef')
        tag = Tag(name='cow')
        session.add(image)
        session.add(tag)
        session.flush()
        image_tag = ImageTag(image_id=image.image_id, tag_id=tag.tag_id)
        session.add(image_tag)
        session.flush()

        response = self.app.patch('/image/%d.json' % image.image_id, data={
            'remove_tag': 'cow',
        })
        eq_(response.status_code, 200)
        body = json.loads(response.data)
        eq_(body['status'], 'ok')

        image_tags = session.query(ImageTag).all()
        eq_(image_tags, [])
