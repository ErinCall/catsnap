from __future__ import unicode_literals

import os
import tempfile
from StringIO import StringIO
import Image as ImageHandler

from catsnap import Client
from catsnap.table.image import Image as ImageTable, ImageResize
from catsnap.image_truck import ImageTruck

RESIZES = {
        'thumbnail': 100,
        'small': 320,
        'medium': 500,
        'large': 1600
        }

class ResizeImage(object):
    @classmethod
    def make_resizes(cls, image):
        contents = ImageTruck.contents_of_filename(image.filename)
        image_handler = ImageHandler.open(StringIO(contents))
        long_side = max(image_handler.size)

        for size, new_long_side in RESIZES.iteritems():
            if new_long_side < long_side:
                cls._resize_image(image, image_handler, size)

    @classmethod
    def _resize_image(cls, image, image_handler, size):
        session = Client().session()

        (width, height) = image_handler.size
        (new_width, new_height) = cls._new_dimensions(width,
                                                      height,
                                                      RESIZES[size])

        print 'resizing to %s' % size
        resized = image_handler.resize((new_width, new_height),
                                       ImageHandler.ANTIALIAS)
        (_, contents_file) = tempfile.mkstemp()
        try:
            resized.save(contents_file, image_handler.format)
            with open(contents_file, 'r') as contents:
                truck = ImageTruck.new_from_stream(
                        contents,
                        cls._content_type_from_format(image_handler.format),
                        suffix=size,
                        filename=image.filename)
                print 'uploading resized image'
                truck.upload()
        finally:
            os.unlink(contents_file)

        resize = ImageResize(image_id=image.image_id,
                             width=new_width,
                             height=new_height,
                             suffix='medium')
        session.add(resize)
        session.flush()

    @classmethod
    def _new_dimensions(cls, width, height, new_long_side):
        if width > height:
            (long_side, short_side) = (width, height)
        else:
            (short_side, long_side) = (width, height)

        aspect_ratio = float(long_side)/float(short_side)
        new_short_side = int(new_long_side/aspect_ratio)

        if width > height:
            (new_width, new_height) = (new_long_side, new_short_side)
        else:
            (new_height, new_width) = (new_long_side, new_short_side)

        return (new_width, new_height)

    @classmethod
    def _content_type_from_format(cls, format):
        return {
            'JPEG': 'image/jpeg',
            'PNG': 'image/png',
            'GIF': 'image/gif',
                }[format]

