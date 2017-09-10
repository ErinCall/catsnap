import time
from wand.image import Image as ImageHandler


class ImageMetadata(object):
    @classmethod
    def image_metadata(cls, contents):
        handler = ImageHandler(blob=contents)
        metadata = handler.metadata
        any_exif = [x for x in list(metadata.keys()) if x.startswith('exif:')]
        if not any_exif:
            return {}

        aperture = metadata.get('exif:FNumber')
        if aperture is not None:
            parts = aperture.split('/')
            if len(parts) == 0:
                aperture = '1/{0}'.format(parts[0])
            else:
                aperture = '1/{0}'.format(float(parts[0]) / float(parts[1]))

        shutter_speed = metadata.get('exif:ExposureTime')

        photographed_at = metadata.get('exif:DateTime')
        if photographed_at is not None:
            photographed_at = time.strftime(
                '%Y-%m-%d %H:%M:%S', time.strptime(
                    photographed_at, '%Y:%m:%d %H:%M:%S'))

        make = metadata.get('exif:Make')
        model = metadata.get('exif:Model')
        if make is not None and model is not None:
            camera = '%s %s' % (make, model)
        else:
            camera = model

        focal_length = metadata.get('exif:FocalLength')
        if focal_length is not None:
            parts = focal_length.split('/')
            if len(parts) == 1:
                focal_length = parts[0]
            else:
                focal_length = float(parts[0]) / float(parts[1])

        iso = metadata.get('exif:ISOSpeedRatings')
        if iso is not None:
            iso = int(iso)

        return {
            'camera': camera,
            'photographed_at': photographed_at,
            'focal_length': focal_length,
            'aperture': aperture,
            'shutter_speed': shutter_speed,
            'iso': iso,
        }
