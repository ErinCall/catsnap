from __future__ import unicode_literals

import os.path
from wand.image import Image as ImageHandler
from mock import patch, MagicMock, Mock, call
from nose.tools import eq_, nottest
from tests import TestCase

from catsnap import Client
from catsnap.image_truck import ImageTruck
from catsnap.table.image import Image as ImageTable, ImageResize
from catsnap.resize_image import ResizeImage


class TestResizeImage(TestCase):
    def test_resize_an_image(self):
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_image_640x427.jpg')
        image_handler = ImageHandler(filename=test_file)
        truck = Mock()
        session = Client().session()
        image = ImageTable(filename='badcafe')
        session.add(image)
        session.flush()

        ResizeImage._resize_image(image, image_handler, truck, 'thumbnail')

        resizes = session.query(ImageResize).all()
        eq_(len(resizes), 1)
        eq_(resizes[0].width, 100)
        eq_(resizes[0].height, 66)
        eq_(resizes[0].suffix, 'thumbnail')

        (args, kwargs) = truck.upload_resize.call_args
        eq_(args[1], 'thumbnail')

    @patch('catsnap.resize_image.ImageHandler')
    def test_resize_a_portrait_image(self, MockImage):
        session = Client().session()
        image_handler = Mock()
        image_handler.size = (427, 640)
        image_handler.format = 'JPEG'
        image = ImageTable(filename='badcafe')
        session.add(image)
        session.flush()

        ResizeImage._resize_image(image, image_handler, Mock(), 'medium')

        resizes = session.query(ImageResize).all()
        eq_(len(resizes), 1)
        eq_(resizes[0].height, 500)
        eq_(resizes[0].width, 333)

    @patch('catsnap.resize_image.ImageHandler')
    @patch('catsnap.resize_image.ResizeImage._resize_image')
    def test_creates_various_resizes(self, resize_image_method, MockImage):
        session = Client().session()
        image = ImageTable(filename='faded')
        session.add(image)
        session.flush()

        truck = ImageTruck('contents', None, None)

        image_handler = MagicMock()
        image_handler.size = (3648, 2736)
        image_handler.clone.return_value = image_handler
        image_handler.__enter__.return_value = image_handler
        MockImage.return_value = image_handler

        ResizeImage.make_resizes(image, truck)

        resize_image_method.assert_has_calls([
            call(image, image_handler, truck, 'thumbnail'),
            call(image, image_handler, truck, 'small'),
            call(image, image_handler, truck, 'medium'),
            call(image, image_handler, truck, 'large'),
        ], any_order=True)

    @patch('catsnap.resize_image.ImageHandler')
    @patch('catsnap.resize_image.ResizeImage._resize_image')
    def test_only_scales_images_down_not_up(self,
                                            resize_image_method,
                                            MockImage):
        image_handler = MagicMock()
        image_handler.size = (360, 360)
        image_handler.clone.return_value = image_handler
        image_handler.__enter__.return_value = image_handler
        MockImage.return_value = image_handler

        session = Client().session()
        image = ImageTable(filename='faded')
        session.add(image)
        session.flush()

        truck = Mock()
        ResizeImage.make_resizes(image, truck)

        resize_image_method.assert_has_calls([
            call(image, image_handler, truck, 'thumbnail'),
            call(image, image_handler, truck, 'small'),
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
        image_handler = ImageHandler(filename=test_file)
        with open(test_file, 'r') as fh:
            truck = ImageTruck.new_from_stream(fh, content_type)
        session = Client().session()
        image = ImageTable(filename='badcafe')
        session.add(image)
        session.flush()

        ResizeImage._resize_image(image, image_handler, truck, 'thumbnail')

        new_key.set_metadata.assert_called_with('Content-Type', content_type)
        resized_contents = new_key.set_contents_from_string.call_args[0][0]

        image_handler = ImageHandler(blob=resized_contents)
        eq_(image_handler.size, resized_size)
