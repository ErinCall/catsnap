from __future__ import unicode_literals

from wand.image import Image as ImageHandler


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
            handler = ImageHandler(blob=contents)
        except IOError:
            return contents
        orientation = handler.metadata.get('exif:Orientation')
        if not orientation:
            return contents

        {
            1: lambda: handler,
            2: lambda: handler.flop(),
            3: lambda: handler.rotate(180),
            4: lambda: handler.flip(),
            5: lambda: handler.flip().rotate(270),
            6: lambda: handler.rotate(270),
            7: lambda: handler.flop().rotate(270),
            8: lambda: handler.rotate(90),
        }[int(orientation)]()

        return handler.make_blob()
