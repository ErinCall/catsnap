from __future__ import unicode_literals

import os
import tempfile
from StringIO import StringIO
import ExifTags
import Image as ImageHandler


class ReorientImage(object):
    """
    takes in arbitrary image contents. The contents may or may not be a jpeg
    with EXIF data indicating an orientation. If it's not a jpeg, or the jpeg
    doesn't have EXIF data, or the exif data doesn't indicate an orientation,
    returns the contents unmodified. However, if the EXIF data indicates an
    orientation, returns new contents that have been rotated/flipped to
    correspond to the listed orientation.

    In the case that an image is reoriented, the returned contents will NOT
    have any EXIF data inside them.

    !!!THIS METHOD IS NOT TESTED!!! Tread carefully.
    """
    @classmethod
    def reorient_image(cls, contents):
        try:
            handler = ImageHandler.open(StringIO(contents))
        except IOError:
            return contents
        exif = getattr(handler, '_getexif', lambda: None)()
        if not exif:
            return handler
        decoded_exif = {ExifTags.TAGS.get(tag, tag): value
                        for (tag, value) in exif.iteritems()}
        orientation = decoded_exif.get('Orientation')
        if not orientation:
            return handler

        reoriented_handler = {
            1: lambda: handler,
            2: lambda: handler.transpose(ImageHandler.FLIP_LEFT_RIGHT),
            3: lambda: handler.transpose(ImageHandler.ROTATE_180),
            4: lambda: handler.transpose(ImageHandler.FLIP_TOP_BOTTOM),
            5: lambda: handler.transpose(ImageHandler.FLIP_TOP_BOTTOM).
            transpose(ImageHandler.ROTATE_270),
            6: lambda: handler.transpose(ImageHandler.ROTATE_270),
            7: lambda: handler.transpose(ImageHandler.FLIP_LEFT_RIGHT).
            transpose(ImageHandler.ROTATE_270),
            8: lambda: handler.transpose(ImageHandler.ROTATE_90),
        }[orientation]()

        (_, contents_file) = tempfile.mkstemp()
        try:
            reoriented_handler.save(contents_file, handler.format)
            with open(contents_file, 'r') as fh:
                return fh.read()
        finally:
            os.unlink(contents_file)
