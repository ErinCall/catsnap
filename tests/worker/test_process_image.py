from mock import patch, Mock
from nose.tools import eq_, nottest, raises
from tests import TestCase
from tests.image_helper import SOME_PNG, EXIF_JPG

from sqlalchemy.orm.exc import NoResultFound
from catsnap import Client
from catsnap.table.image import Image, ImageContents
from catsnap.table.task_transaction import TaskTransaction
from catsnap.worker.tasks import process_image


class TestProcessImage(TestCase):
    @patch('catsnap.worker.tasks.ImageTruck')
    @patch('catsnap.worker.tasks.ReorientImage')
    def test_reorients_images(self, ReorientImage, ImageTruck):
        transaction_id = TaskTransaction.new_id()
        image_data = self.image_data()
        (image, contents) = self.setup_contents(image_data)
        truck = Mock()
        truck.contents = image_data
        ImageTruck.return_value = truck
        ReorientImage.reorient_image.return_value = image_data

        process_image(transaction_id, contents.image_contents_id)

        ReorientImage.reorient_image.assert_called_with(image_data)

    @patch('catsnap.worker.tasks.ImageTruck')
    def test_uploads_to_s3(self, ImageTruck):
        transaction_id = TaskTransaction.new_id()
        image_data = self.image_data()
        (image, contents) = self.setup_contents(image_data)
        truck = Mock()
        truck.contents = image_data
        ImageTruck.return_value = truck

        process_image(transaction_id, contents.image_contents_id)

        ImageTruck.assert_called_with(image_data, 'image/png', None)
        truck.upload.assert_called_with()

    @patch('catsnap.worker.tasks.ImageTruck')
    @patch('catsnap.worker.tasks.ResizeImage')
    def test_makes_resizes(self, ResizeImage, ImageTruck):
        transaction_id = TaskTransaction.new_id()
        image_data = self.image_data()
        (image, contents) = self.setup_contents(image_data)
        truck = Mock()
        truck.contents = image_data
        ImageTruck.return_value = truck

        process_image(transaction_id, contents.image_contents_id)

        call_args = ResizeImage.make_resizes.call_args
        eq_(call_args[0][0], image)
        eq_(call_args[0][1], truck)
        # the 3rd arg is the after_upload callback, which we can't assert well
        eq_(len(call_args[0]), 3)

    @patch('catsnap.worker.tasks.ImageTruck')
    def test_deletes_processed_contents(self, ImageTruck):
        session = Client().session()
        transaction_id = TaskTransaction.new_id()
        image_data = self.image_data()
        (image, contents) = self.setup_contents(image_data)
        truck = Mock()
        truck.contents = image_data
        ImageTruck.return_value = truck

        process_image(transaction_id, contents.image_contents_id)

        session = Client().session()
        contents = session.query(ImageContents).all()

        eq_(contents, [])

    # After an async upload, the page JS wants an image to display. It wants
    # thumbnail, ideally, so this test should really show that thumbnail
    # happens first.
    @patch('catsnap.worker.tasks.ImageTruck')
    @patch('catsnap.worker.tasks.ResizeImage')
    def test_resize_happens_before_main_upload(
            self, ResizeImage, ImageTruck):
        class StopDoingThingsNow(Exception): pass

        transaction_id = TaskTransaction.new_id()
        image_data = self.image_data()
        (image, contents) = self.setup_contents(image_data)
        truck = Mock()
        truck.contents = image_data
        truck.upload.side_effect = StopDoingThingsNow
        ImageTruck.return_value = truck

        try:
            process_image(transaction_id, contents.image_contents_id)
        except StopDoingThingsNow:
            pass

        call_args = ResizeImage.make_resizes.call_args
        eq_(call_args[0][0], image)
        eq_(call_args[0][1], truck)
        # the 3rd arg is the after_upload callback, which we can't assert well
        eq_(len(call_args[0]), 3)

    # ResizeImage and ReorientImage are just stubbed for speed;
    # the test image with intact EXIF data is quite large
    @patch('catsnap.worker.tasks.ResizeImage')
    @patch('catsnap.worker.tasks.ReorientImage')
    @patch('catsnap.worker.tasks.ImageTruck')
    def test_calculates_metadata(self, ImageTruck, ReorientImage, ResizeImage):
        session = Client().session()
        with open(EXIF_JPG, 'br') as fh:
            image_data = fh.read()

        (image, contents) = self.setup_contents(image_data)
        truck = Mock()
        truck.contents = image_data
        ImageTruck.return_value = truck

        transaction_id = TaskTransaction.new_id()
        session.flush()
        process_image(transaction_id, contents.image_contents_id)

        image = session.query(Image).\
            filter(Image.image_id == image.image_id)\
            .one()

        eq_(image.camera, 'SAMSUNG NX210')
        eq_(image.photographed_at, '2013-05-03 09:17:02')
        eq_(image.aperture, '1/4.5')
        eq_(image.shutter_speed, '1/800')
        eq_(image.focal_length, 30.0)
        eq_(image.iso, 200)

    @nottest
    def image_data(self):
        with open(SOME_PNG, 'br') as fh:
            return fh.read()

    @nottest
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

