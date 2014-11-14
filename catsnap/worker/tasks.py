from __future__ import unicode_literals, absolute_import

import time
from datetime import timedelta
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
    def run(self, image_id, suffix=None):
        session = Client().session()
        now = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        try:
            image = session.query(Image).\
                filter((Image.created_at - timedelta(hours=1)) < now).\
                filter(Image.image_id == image_id).\
                one()
        except NoResultFound:
            session.rollback()
            logger.error('No unexpired result found for image_id {0}. '
                         'Skipping.'.format(image_id))
            return

        filename = image.filename
        print repr(suffix)
        if suffix is not None:
            filename = '{0}_{1}'.format(filename, suffix)

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
    Invalidate().delay(image.image_id)

    for attr, value in metadata.iteritems():
        setattr(image, attr, value)
    session.add(image)
    session.delete(contents)
