from __future__ import unicode_literals, absolute_import

from boto.cloudfront.exception import CloudFrontServerError
from catsnap.image_metadata import ImageMetadata
from catsnap.image_truck import ImageTruck
from catsnap.reorient_image import ReorientImage
from catsnap.resize_image import ResizeImage
from catsnap.table.image import Image, ImageContents
from catsnap.worker import worker
from catsnap import Client

class Invalidate(worker.Task):
    def run(self, filename):
        config = Client().config()
        try:
            distro_id = config['cloudfront_distribution_id']
            Client().get_cloudfront().create_invalidation_request(
                distro_id, filename)
        except KeyError:
            pass
        except CloudFrontServerError as e:
            if e.error_code == 'TooManyInvalidationsInProgress':
                self.retry(e)
            else:
                raise

@worker.task(bind=True)
def process_image(self, image_contents_id):
    session = Client().session()
    contents = session.query(ImageContents).\
        filter(ImageContents.image_contents_id == image_contents_id).\
        one()
    image = session.query(Image).\
        filter(Image.image_id == contents.image_id).\
        one()

    truck = ImageTruck(
        contents.contents, contents.content_type, image.source_url)
    metadata = ImageMetadata.image_metadata(truck.contents)
    truck.contents = ReorientImage.reorient_image(truck.contents)
    truck.upload()
    ResizeImage.make_resizes(image, truck)

    for attr, value in metadata.iteritems():
        setattr(image, attr, value)
    session.add(image)
    session.delete(contents)
