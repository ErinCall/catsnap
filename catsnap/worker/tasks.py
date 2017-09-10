

import json
import time
from datetime import timedelta
from sqlalchemy.orm.exc import NoResultFound
from boto.cloudfront.exception import CloudFrontServerError
from celery.utils.log import get_task_logger
from catsnap.image_metadata import ImageMetadata
from catsnap.image_truck import ImageTruck
from catsnap.worker.redis_websocket_bridge import redis, REDIS_CHANNEL
from catsnap.reorient_image import ReorientImage
from catsnap.resize_image import ResizeImage
from catsnap.table.image import Image, ImageContents
from catsnap.worker import worker, queued_tasks
from catsnap.db_redis_coordination import delay, wait_for_transaction
from catsnap import Client

logger = get_task_logger(__name__)

class Invalidate(worker.Task):
    @wait_for_transaction
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
        print(repr(suffix))
        if suffix is not None:
            filename = '{0}_{1}'.format(filename, suffix)

        config = Client().config()
        try:
            distro_id = config['aws.cloudfront_distribution_id']
            Client().get_cloudfront().create_invalidation_request(
                distro_id, [filename])
        except KeyError:
            pass
        except CloudFrontServerError as e:
            if e.error_code == 'TooManyInvalidationsInProgress':
                self.retry(exc=e)
            else:
                raise

@worker.task(bind=True)
@wait_for_transaction
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
    truck.filename = image.filename
    metadata = ImageMetadata.image_metadata(truck.contents)
    truck.contents = ReorientImage.reorient_image(truck.contents)
    def after_upload(size):
        redis.publish(REDIS_CHANNEL, json.dumps({
            'task_id': self.request.id,
            'suffix': size,
        }))
    ResizeImage.make_resizes(image, truck, after_upload)

    print("uploading original image")
    truck.upload()
    redis.publish(REDIS_CHANNEL, json.dumps({
        'task_id': self.request.id,
        'suffix': '',
    }))

    delay(queued_tasks, Invalidate(), image.image_id)

    for attr, value in metadata.items():
        setattr(image, attr, value)
    session.add(image)
    session.delete(contents)
