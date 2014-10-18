from __future__ import unicode_literals

import os
from mock import patch, Mock
from nose.tools import eq_

from tests import TestCase
from catsnap import Client
from catsnap.table.image import Image, ImageContents
from catsnap.worker.tasks import process_image


class TestProcessImage(TestCase):
    @patch('catsnap.worker.tasks.ImageTruck')
    @patch('catsnap.worker.tasks.ReorientImage')
    def test_reorients_images(self, ReorientImage, ImageTruck):
        image_data = self.image_data()
        (image, contents) = self.setup_contents(image_data)
        truck = Mock()
        truck.contents = image_data
        ImageTruck.return_value = truck
        ReorientImage.reorient_image.return_value = image_data

        process_image(contents.image_contents_id)

        ReorientImage.reorient_image.assert_called_with(image_data)

    @patch('catsnap.worker.tasks.ImageTruck')
    def test_uploads_to_s3(self, ImageTruck):
        image_data = self.image_data()
        (image, contents) = self.setup_contents(image_data)
        truck = Mock()
        truck.contents = image_data
        ImageTruck.return_value = truck

        process_image(contents.image_contents_id)

        ImageTruck.assert_called_with(image_data, 'image/png', None)
        truck.upload.assert_called_with()

    @patch('catsnap.worker.tasks.ImageTruck')
    @patch('catsnap.worker.tasks.ResizeImage')
    def test_makes_resizes(self, ResizeImage, ImageTruck):
        image_data = self.image_data()
        (image, contents) = self.setup_contents(image_data)
        truck = Mock()
        truck.contents = image_data
        ImageTruck.return_value = truck

        process_image(contents.image_contents_id)

        ResizeImage.make_resizes.assert_called_with(image, truck)

    @patch('catsnap.worker.tasks.ImageTruck')
    def test_deletes_processed_contents(self, ImageTruck):
        image_data = self.image_data()
        (image, contents) = self.setup_contents(image_data)
        truck = Mock()
        truck.contents = image_data
        ImageTruck.return_value = truck

        process_image(contents.image_contents_id)

        session = Client().session()
        contents = session.query(ImageContents).all()

        eq_(contents, [])

    # ResizeImage and ReorientImage are just stubbed for speed;
    # the test image with intact EXIF data is quite large
    @patch('catsnap.worker.tasks.ResizeImage')
    @patch('catsnap.worker.tasks.ReorientImage')
    @patch('catsnap.worker.tasks.ImageTruck')
    def test_calculates_metadata(self, ImageTruck, ReorientImage, ResizeImage):
        test_file = os.path.join(os.path.dirname(__file__),
                                 '..',
                                 'test_image_5472x3648.jpg')
        with open(test_file, 'r') as fh:
            image_data = fh.read()

        (image, contents) = self.setup_contents(image_data)
        truck = Mock()
        truck.contents = image_data
        ImageTruck.return_value = truck

        process_image(contents.image_contents_id)

        session = Client().session()
        image = session.query(Image).\
            filter(Image.image_id == image.image_id)\
            .one()

        eq_(image.camera, 'SAMSUNG NX210')
        eq_(image.photographed_at, '2013-05-03 09:17:02')
        eq_(image.aperture, '1/4.5')
        eq_(image.shutter_speed, '1/800')
        eq_(image.focal_length, 30.0)
        eq_(image.iso, 200)

    def image_data(self):
        test_file = os.path.join(os.path.dirname(__file__),
                                 '..',
                                 'test_image_592x821.png')
        with open(test_file, 'r') as fh:
            return fh.read()

    def setup_contents(self, image_data):
        session = Client().session()
        image = Image(filename='CA7F00D')
        session.add(image)
        session.flush()
        contents = ImageContents(
            image_id=image.image_id,
            contents=image_data,
            content_type="image/png",
        )
        session.add(contents)
        session.flush()

        return (image, contents)

