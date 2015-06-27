from __future__ import unicode_literals

import json
from mock import patch, Mock
from tests import TestCase, logged_in
from nose.tools import eq_
from catsnap import Client
from catsnap.table.image import Image, ImageContents
from catsnap.worker.tasks import process_image


class TestReprocess(TestCase):
    @logged_in
    @patch('catsnap.web.controllers.image.delay')
    @patch('catsnap.web.controllers.image.ImageTruck')
    def test_reprocess_image(self, ImageTruck, delay):
        truck = Mock()
        truck.contents = b'a party in my mouth and everyone is invited'
        truck.content_type = 'image/jpeg'
        ImageTruck.new_from_image.return_value = truck

        session = Client().session()
        image = Image(filename="facecafe")
        session.add(image)
        session.flush()

        response = self.app.post('/image/reprocess/{0}.json'.format(image.image_id))
        eq_(response.status_code, 200)
        body = json.loads(response.data)
        eq_(body, {'status': 'ok'})

        contents = session.query(ImageContents).one()
        eq_(image.image_id, contents.image_id)
        eq_(contents.contents, 'a party in my mouth and everyone is invited')
        eq_(contents.content_type, 'image/jpeg')

        delay.assert_called_with([], process_image, contents.image_contents_id)
