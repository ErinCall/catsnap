from nose.tools import eq_
from tests import TestCase
from tests.image_helper import EXIF_JPG, MALFORMED_JPG, SOME_GIF

from catsnap.image_metadata import ImageMetadata


class TestImageMetadata(TestCase):
    def test_get_image_metadata(self):
        with open(EXIF_JPG, 'br') as fh:
            contents = fh.read()

        metadata = ImageMetadata.image_metadata(contents)

        eq_(metadata, {
            'camera': 'SAMSUNG NX210',
            'photographed_at': '2013-05-03 09:17:02',
            'aperture': '1/4.5' ,
            'shutter_speed': '1/800',
            'focal_length': 30.0,
            'iso': 200,
            })

    def test_get_image_metadata_when_there_is_none(self):
        with open(SOME_GIF, 'br') as fh:
            contents = fh.read()

        metadata = ImageMetadata.image_metadata(contents)

        eq_(metadata, {})

    def test_handles_oddly_malformed_metadata(self):
        with open(MALFORMED_JPG, 'br') as fh:
            contents = fh.read()

        metadata = ImageMetadata.image_metadata(contents)

        eq_(metadata['aperture'], None)
