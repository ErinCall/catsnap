from __future__ import unicode_literals, absolute_import

from boto.cloudfront.exception import CloudFrontServerError
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
