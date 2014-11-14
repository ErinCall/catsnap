from __future__ import unicode_literals

from mock import patch, Mock
from nose.tools import raises
from boto.cloudfront.exception import CloudFrontServerError
from tests import TestCase, with_settings

from catsnap import Client
from catsnap.worker.tasks import Invalidate

class TestInvalidate(TestCase):
    @with_settings(cloudfront_distribution_id='CRIPESKAREN')
    @patch('catsnap.worker.tasks.Client')
    def test_toomanyinvalidation_errors_are_ignored(self, MockClient):
        error = CloudFrontServerError(400, 'Bad Request')
        error.error_code = 'TooManyInvalidationsInProgress'

        cloudfront = Mock()
        cloudfront.create_invalidation_request.side_effect = error

        config = Client().config()
        client = Mock()
        client.config.return_value = config
        client.get_cloudfront.return_value = cloudfront
        MockClient.return_value = client

        invalidate = NeverCalledDirectlyInvalidate()
        invalidate.retry = Mock()
        invalidate('abad1dea')

        invalidate.retry.assert_called_with(exc=error)

    @raises(CloudFrontServerError)
    @with_settings(cloudfront_distribution_id='SHEESHJESSICA')
    @patch('catsnap.worker.tasks.Client')
    def test_unknown_cloudfront_errors_reraise(self, MockClient):
        error = CloudFrontServerError(400, 'Bad Request')
        error.error_code = 'CloudFrontHatesYouToday'

        cloudfront = Mock()
        cloudfront.create_invalidation_request.side_effect = error

        config = Client().config()
        client = Mock()
        client.config.return_value = config
        client.get_cloudfront.return_value = cloudfront
        MockClient.return_value = client

        Invalidate()('abad1dea')

# Normally, if you call retry() from inside a task that was invoked directly
# (rather than inside an async worker), Celery will re-raise the original
# exception. This injects itself into Celery's innards so that won't happen.
class NeverCalledDirectlyInvalidate(Invalidate):
    def _get_request(self):
        request = super(NeverCalledDirectlyInvalidate, self)._get_request()
        request.called_directly = False
        return request
