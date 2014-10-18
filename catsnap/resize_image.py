from __future__ import unicode_literals

from wand.image import Image as ImageHandler

from catsnap import Client
from catsnap.table.image import ImageResize

RESIZES = {
        'thumbnail': 100,
        'small': 320,
        'medium': 500,
        'large': 1600
        }

class ResizeImage(object):
    @classmethod
    def make_resizes(cls, image, truck):
        contents = truck.contents
        image_handler = ImageHandler(blob=contents)
        long_side = max(image_handler.size)

        for size, new_long_side in RESIZES.iteritems():
            if new_long_side < long_side:
                cls._resize_image(image, image_handler, truck, size)

    @classmethod
    def _resize_image(cls, image, image_handler, truck, size):
        session = Client().session()

        (width, height) = image_handler.size
        (new_width, new_height) = cls._new_dimensions(width,
                                                      height,
                                                      RESIZES[size])

        print 'resizing to %s' % size
        image_handler.resize(new_width, new_height,
                             filter='hamming')
        print 'uploading resized image'
        truck.upload_resize(image_handler.make_blob(), size)

        resize = ImageResize(image_id=image.image_id,
                             width=new_width,
                             height=new_height,
                             suffix=size)
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
