from __future__ import unicode_literals

import time
from StringIO import StringIO
from fractions import Fraction
import Image as ImageHandler
import ExifTags

class ImageMetadata(object):
    @classmethod
    def image_metadata(cls, contents):
        handler = ImageHandler.open(StringIO(contents))
        exif = handler._getexif()
        if exif is None:
            return {}
        decoded_exif = {ExifTags.TAGS.get(tag, tag): value
                for (tag, value) in exif.iteritems()}

        f_number = decoded_exif.get('FNumber')
        if f_number is not None:
            (aperture_numerator, aperture_denominator) = f_number
            aperture = '1/%.1f' % (aperture_numerator/aperture_denominator)

        shutter_speed = decoded_exif.get('ExposureTime')
        if shutter_speed is not None:
            shutter_speed = cls._calculate_shutter_speed(*shutter_speed)

        photographed_at = decoded_exif.get('DateTime')
        if photographed_at is not None:
            photographed_at = time.strftime('%Y-%d-%m %H:%M:%S', time.strptime(
                    photographed_at, '%Y:%d:%m %H:%M:%S'))

        make = decoded_exif.get('Make')
        model = decoded_exif.get('Model')
        if make is not None and model is not None:
            camera = '%s %s' % (make, model)
        else:
            camera = model

        focal_length = decoded_exif.get('FocalLength')
        if focal_length is not None:
            focal_length = int(Fraction(*(focal_length)))
        return {
                'camera': camera,
                'photographed_at': photographed_at,
                'focal_length': focal_length,
                'aperture': aperture,
                'shutter_speed': shutter_speed,
                'iso': decoded_exif.get('ISOSpeedRatings'),
                }

    @classmethod
    def _calculate_shutter_speed(cls, numerator, denominator):
        rational = Fraction(numerator, denominator)
        if rational.denominator == 1:
            return unicode(rational.numerator)
        else:
            return '%d/%d' % (numerator, denominator)
