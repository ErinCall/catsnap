from __future__ import unicode_literals

import os
import tempfile
from StringIO import StringIO
import ExifTags
from wand.image import Image as ImageHandler


class ReorientImage(object):
    """
    takes in arbitrary image contents. The contents may or may not be a jpeg
    with EXIF data indicating an orientation. If it's not a jpeg, or the jpeg
    doesn't have EXIF data, or the exif data doesn't indicate an orientation,
    returns the contents unmodified. However, if the EXIF data indicates an
    orientation, returns new contents that have been rotated/flipped to
    correspond to the listed orientation.

    In the case that an image is reoriented, the returned contents will have
    EXIF data inside them, but the orientation tag will be wrong. :(

    !!!THIS METHOD IS NOT TESTED!!! Tread carefully.
    """
    @classmethod
    def reorient_image(cls, contents):
        handler = ImageHandler(blob=contents)
        orientation = handler.metadata.get('exif:Orientation')
        if not orientation:
            return contents

        {
            '1': lambda: None,
            '2': lambda: handler.flop(),
            '3': lambda: handler.rotate(degree=180),
            '4': lambda: handler.flip(),
            '5': lambda: handler.flip().rotate(degree=90),
            '6': lambda: handler.rotate(degree=90),
            '7': lambda: handler.flop().rotate(degree=90),
            '8': lambda: handler.rotate(degree=270),
        }[orientation]()

        return handler.make_blob()
