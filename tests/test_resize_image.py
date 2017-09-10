import os.path
from wand.image import Image as ImageHandler
from mock import patch, Mock, call
from nose.tools import eq_, nottest
from tests import TestCase
from tests.image_helper import SMALL_JPG, SOME_GIF, SOME_PNG

from catsnap import Client
from catsnap.image_truck import ImageTruck
from catsnap.table.image import Image as ImageTable, ImageResize
from catsnap.resize_image import ResizeImage

class TestResizeImage(TestCase):
    def test_resize_an_image(self):
        image_handler = ImageHandler(filename=SMALL_JPG)
        truck = Mock()
        session = Client().session()
        image = ImageTable(filename='badcafe')
        session.add(image)
        session.flush()

        after_upload = Mock()
        ResizeImage._resize_image(image,
                                  image_handler,
                                  truck,
                                  'thumbnail',
                                  after_upload)

        resizes = session.query(ImageResize).all()
        eq_(len(resizes), 1)
        eq_(resizes[0].width, 100)
        eq_(resizes[0].height, 66)
        eq_(resizes[0].suffix, 'thumbnail')

        (args, kwargs) = truck.upload_resize.call_args
        eq_(args[1], 'thumbnail')
        after_upload.assert_called_once_with('thumbnail')

    @patch('catsnap.resize_image.ImageHandler')
    def test_resize_a_portrait_image(self, MockImage):
        session = Client().session()
        image_handler = Mock()
        image_handler.size = (427, 640)
        image_handler.format = 'JPEG'
        image = ImageTable(filename='badcafe')
        session.add(image)
        session.flush()

        after_upload = Mock()
        ResizeImage._resize_image(image,
                                  image_handler,
                                  Mock(),
                                  'medium',
                                  after_upload)

        resizes = session.query(ImageResize).all()
        eq_(len(resizes), 1)
        eq_(resizes[0].height, 500)
        eq_(resizes[0].width, 333)

        after_upload.assert_called_once_with('medium')

    @patch('catsnap.resize_image.ImageHandler')
    @patch('catsnap.resize_image.ResizeImage._resize_image')
    def test_creates_various_resizes(self, resize_image_method, MockImage):
        session = Client().session()
        image = ImageTable(filename='faded')
        session.add(image)
        session.flush()

        truck = ImageTruck(b'contents', None, None)

        image_handler = Mock()
        image_handler.size = (3648, 2736)
        MockImage.return_value = image_handler
        after_upload = Mock()

        ResizeImage.make_resizes(image, truck, after_upload)

        resize_image_method.assert_has_calls([
            call(image, image_handler, truck, 'thumbnail', after_upload),
            call(image, image_handler, truck, 'small', after_upload),
            call(image, image_handler, truck, 'medium', after_upload),
            call(image, image_handler, truck, 'large', after_upload),
        ])

    @patch('catsnap.resize_image.ImageHandler')
    @patch('catsnap.resize_image.ResizeImage._resize_image')
    def test_only_scales_images_down_not_up(self,
                                            resize_image_method,
                                            MockImage):
        image_handler = Mock()
        image_handler.size = (360, 360)
        MockImage.return_value = image_handler

        session = Client().session()
        image = ImageTable(filename='faded')
        session.add(image)
        session.flush()

        truck = Mock()
        after_upload = Mock()
        ResizeImage.make_resizes(image, truck, after_upload)

        resize_image_method.assert_has_calls([
            call(image, image_handler, truck, 'thumbnail', after_upload),
            call(image, image_handler, truck, 'small', after_upload),
            ], any_order=True)

    @patch('catsnap.Client.bucket')
    def test_handles_jpegs(self, bucket_method):
        self.file_type_test(bucket_method,
                            SMALL_JPG,
                            'image/jpeg',
                            (100, 66))

    @patch('catsnap.Client.bucket')
    def test_handles_pngs(self, bucket_method):
        self.file_type_test(bucket_method,
                            SOME_PNG,
                            'image/png',
                            (72, 100))

    @patch('catsnap.Client.bucket')
    def test_handles_gifs(self, bucket_method):
        self.file_type_test(bucket_method,
                            SOME_GIF,
                            'image/gif',
                            (100, 64))

    @nottest
    def file_type_test(self,
                       bucket_method,
                       test_file,
                       content_type,
                       resized_size):
        bucket = Mock()
        bucket_method.return_value = bucket
        new_key = Mock()
        bucket.new_key.return_value = new_key
        image_handler = ImageHandler(filename=test_file)
        truck = ImageTruck.new_from_file(test_file)
        session = Client().session()
        image = ImageTable(filename='badcafe')
        session.add(image)
        session.flush()
        after_upload = Mock()

        ResizeImage._resize_image(image,
                                  image_handler,
                                  truck,
                                  'thumbnail',
                                  after_upload)

        new_key.set_metadata.assert_called_with('Content-Type', content_type)
        resized_contents = new_key.set_contents_from_string.call_args[0][0]

        image_handler = ImageHandler(blob=resized_contents)
        eq_(image_handler.size, resized_size)

        after_upload.assert_called_once_with('thumbnail')
