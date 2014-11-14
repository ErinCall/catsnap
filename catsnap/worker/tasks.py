from __future__ import unicode_literals, absolute_import

from sqlalchemy.orm.exc import NoResultFound
from boto.cloudfront.exception import CloudFrontServerError
from celery.utils.log import get_task_logger
from catsnap.image_metadata import ImageMetadata
from catsnap.image_truck import ImageTruck
from catsnap.reorient_image import ReorientImage
from catsnap.resize_image import ResizeImage
from catsnap.table.image import Image, ImageContents
from catsnap.worker import worker
from catsnap import Client

logger = get_task_logger(__name__)

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
                self.retry(exc=e)
            else:
                raise

@worker.task(bind=True)
def process_image(self, image_contents_id):
    session = Client().session()
    try:
        contents = session.query(ImageContents).\
            filter(ImageContents.image_contents_id == image_contents_id).\
            one()
    except NoResultFound:
        session.rollback()
        logger.error('No result found for image_contents_id {0}. Aborting.'.
                     format(image_contents_id))
        return

    image = session.query(Image).\
        filter(Image.image_id == contents.image_id).\
        one()

    truck = ImageTruck(
        contents.contents, contents.content_type, image.source_url)
    metadata = ImageMetadata.image_metadata(truck.contents)
    truck.contents = ReorientImage.reorient_image(truck.contents)
    ResizeImage.make_resizes(image, truck)
    print "uploading original image"
    truck.upload()

    for attr, value in metadata.iteritems():
        setattr(image, attr, value)
    session.add(image)
    session.delete(contents)
