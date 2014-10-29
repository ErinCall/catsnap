from __future__ import unicode_literals

import os.path

SOME_GIF = os.path.join(os.path.dirname(__file__), 'test_image_500x319.gif')
EXIF_JPG = os.path.join(os.path.dirname(__file__), 'test_image_5472x3648.jpg')
SOME_PNG = os.path.join(os.path.dirname(__file__), 'test_image_592x821.png')
SMALL_JPG = os.path.join(os.path.dirname(__file__), 'test_image_640x427.jpg')
MALFORMED_JPG = os.path.join(os.path.dirname(__file__),
                             'test_image_malformed_exif.jpg')

