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

    # After an async upload, the page JS starts checking for the worker's
    # completion. Ideally, it wants the thumbnail image. For very small
    # images, though, there won't even be a thumbnail, so the JS needs to be
    # able to fall back to the original size. Doing that requires that
    # "original exists and thumbnail does not" must mean "thumbnail won't
    # exist."
    # There's still a conceivable race condition: [check_thumbnail,
    # upload_thumbnail, upload_original, check_original]. However, it should be
    # sufficiently rare: There's no deliberate delay between check_thumbnail
    # and check_original, while there is some resize-processing time between
    # upload_thumbnail and upload_original, or if there's just thumbnail and
    # original, original must be close enough to thumbnail size that it won't
    # be a big deal if the race condition does hit.
    @patch('catsnap.worker.tasks.ImageTruck')
    @patch('catsnap.worker.tasks.ResizeImage')
    def test_resize_happens_before_main_upload(
            self, ResizeImage, ImageTruck):
        class StopDoingThingsNow(StandardError): pass

        image_data = self.image_data()
        (image, contents) = self.setup_contents(image_data)
        truck = Mock()
        truck.contents = image_data
        truck.upload.side_effect = StopDoingThingsNow
        ImageTruck.return_value = truck

        try:
            process_image(contents.image_contents_id)
        except StopDoingThingsNow:
            pass

        ResizeImage.make_resizes.assert_called_with(image, truck)

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

