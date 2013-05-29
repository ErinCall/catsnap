from __future__ import unicode_literals

import os.path
from nose.tools import eq_
from tests import TestCase

from catsnap.image_metadata import ImageMetadata


class TestImageMetadata(TestCase):
    def test_get_image_metadata(self):
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_image_5472x3648.jpg')
        with open(test_file, 'r') as fh:
            contents = fh.read()

        metadata = ImageMetadata.image_metadata(contents)

        eq_(metadata, {
            'camera': 'SAMSUNG NX210',
            'photographed_at': '2013-05-03 09:17:02',
            'aperture': '1/4.0',
            'shutter_speed': '1/800',
            'focal_length': 30,
            'iso': 200,
            })

    def test_get_image_metadata_when_there_is_none(self):
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_image_500x319.gif')
        with open(test_file, 'r') as fh:
            contents = fh.read()

        metadata = ImageMetadata.image_metadata(contents)

        eq_(metadata, {})

    def test_calculate_shutter_speed(self):
        eq_(ImageMetadata._calculate_shutter_speed(1, 800), '1/800')
        eq_(ImageMetadata._calculate_shutter_speed(50, 10), '5')
