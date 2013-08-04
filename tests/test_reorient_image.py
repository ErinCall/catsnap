from __future__ import unicode_literals

import os.path
from wand.image import Image as ImageHandler
from mock import patch, MagicMock, Mock, call
from nose.tools import eq_, nottest
from tests import TestCase

from catsnap.reorient_image import ReorientImage


class TestReorientImage(TestCase):
    def test_reorient_an_image(self):
        test_file = os.path.join(os.path.dirname(__file__),
                                 'test_image_with_orientation_tag.jpg')
        with open(test_file, 'r') as fh:
            contents = fh.read()

        reoriented_contents = ReorientImage.reorient_image(contents)
        handler = ImageHandler(blob=reoriented_contents)
        eq_(handler.size, (3648, 5472))
