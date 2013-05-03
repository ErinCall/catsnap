from __future__ import unicode_literals

import StringIO
import tempfile
import os.path
import Image as ImageHandler
from requests.exceptions import HTTPError
from mock import patch, MagicMock, Mock, call
from nose.tools import eq_, raises, nottest
from nose.plugins.skip import SkipTest
from tests import TestCase, with_settings

from catsnap import Client
from catsnap.table.image import Image as ImageTable, ImageResize
from catsnap.resize_image import ResizeImage

class TestResizeImage(TestCase):
    @patch('catsnap.resize_image.ImageTruck')
    def test_resize_an_image(self, MockImageTruck):
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_image_640x427.jpg')
        image_handler = ImageHandler.open(test_file)
        truck = Mock()
        MockImageTruck.new_from_stream.return_value = truck
        session = Client().session()
        image = ImageTable(filename='badcafe')
        session.add(image)
        session.flush()

        ResizeImage._resize_image(image, image_handler, 'medium')

        resizes = session.query(ImageResize).all()
        eq_(len(resizes), 1)
        eq_(resizes[0].width, 500)
        eq_(resizes[0].height, 333)
        eq_(resizes[0].suffix, 'medium')

        eq_(MockImageTruck.new_from_stream.call_count, 1)
        MockImageTruck.new_from_stream.assert_called_once()
        (args, kwargs) = MockImageTruck.new_from_stream.call_args
        eq_(kwargs['filename'], 'badcafe')
        truck.upload.assert_called_once_with()

    @patch('catsnap.resize_image.ImageHandler')
    @patch('catsnap.resize_image.ImageTruck')
    def test_resize_a_portrait_image(self, MockImageTruck, MockImage):
        session = Client().session()
        image_handler = Mock()
        image_handler.size = (427, 640)
        image_handler.format = 'JPEG'
        image = ImageTable(filename='badcafe')
        session.add(image)
        session.flush()

        ResizeImage._resize_image(image, image_handler, 'medium')

        resizes = session.query(ImageResize).all()
        eq_(len(resizes), 1)
        eq_(resizes[0].height, 500)
        eq_(resizes[0].width, 333)

    @patch('catsnap.resize_image.ImageTruck')
    @patch('catsnap.resize_image.ImageHandler')
    @patch('catsnap.resize_image.ResizeImage._resize_image')
    def test_creates_various_resizes(self,
                                     resize_image_method,
                                     MockImage,
                                     MockImageTruck):
        session = Client().session()
        image = ImageTable(filename='faded')
        session.add(image)
        session.flush()

        image_handler = Mock()
        image_handler.size = (3648, 2736)
        MockImage.open.return_value = image_handler

        ResizeImage.make_resizes(image.image_id)

        resize_image_method.assert_has_calls([
            call(image, image_handler, 'thumbnail'),
            call(image, image_handler, 'small'),
            call(image, image_handler, 'medium'),
            call(image, image_handler, 'large'),
            ], any_order=True)

    @patch('catsnap.resize_image.ImageHandler')
    @patch('catsnap.resize_image.ResizeImage._resize_image')
    @patch('catsnap.resize_image.ImageTruck')
    def test_only_scales_images_down_not_up(self,
                                            MockImageTruck,
                                            resize_image_method,
                                            MockImage):
        image_handler = Mock()
        image_handler.size = (360, 360)
        MockImage.open.return_value = image_handler

        session = Client().session()
        image = ImageTable(filename='faded')
        session.add(image)
        session.flush()

        ResizeImage.make_resizes(image.image_id)

        resize_image_method.assert_has_calls([
            call(image, image_handler, 'thumbnail'),
            call(image, image_handler, 'small'),
            ], any_order=True)

    @patch('catsnap.Client.bucket')
    def test_handles_jpegs(self, bucket_method):
        self.file_type_test(bucket_method,
                            'test_image_640x427.jpg',
                            'image/jpeg',
                            (100, 66))

    @patch('catsnap.Client.bucket')
    def test_handles_pngs(self, bucket_method):
        self.file_type_test(bucket_method,
                            'test_image_592x821.png',
                            'image/png',
                            (72, 100))

    @patch('catsnap.Client.bucket')
    def test_handles_gifs(self, bucket_method):
        self.file_type_test(bucket_method,
                            'test_image_500x319.gif',
                            'image/gif',
                            (100, 63))

    @nottest
    def file_type_test(self,
                       bucket_method,
                       test_file_name,
                       content_type,
                       resized_size):
        bucket = Mock()
        bucket_method.return_value = bucket
        new_key = Mock()
        bucket.new_key.return_value = new_key
        test_file = os.path.join(os.path.dirname(__file__), test_file_name)
        image_handler = ImageHandler.open(test_file)
        session = Client().session()
        image = ImageTable(filename='badcafe')
        session.add(image)
        session.flush()

        ResizeImage._resize_image(image, image_handler, 'thumbnail')

        new_key.set_metadata.assert_called_with('Content-Type', content_type)
        resized_contents = new_key.set_contents_from_string.call_args[0][0]

        image_handler = ImageHandler.open(StringIO.StringIO(resized_contents))
        eq_(image_handler.size, resized_size)
