from __future__ import unicode_literals

import time
from mock import patch, Mock
from nose.tools import raises
from boto.cloudfront.exception import CloudFrontServerError
from tests import TestCase, with_settings

from catsnap import Client
from catsnap.table.image import Image
from catsnap.table.task_transaction import TaskTransaction
from catsnap.worker.tasks import Invalidate

class TestInvalidate(TestCase):
    @with_settings(aws={'cloudfront_distribution_id': 'CRIPESKAREN'})
    @patch('catsnap.worker.tasks.Client')
    def test_toomanyinvalidation_errors_cause_retry(self, MockClient):
        error = CloudFrontServerError(400, 'Bad Request')
        error.error_code = 'TooManyInvalidationsInProgress'

        cloudfront = Mock()
        cloudfront.create_invalidation_request.side_effect = error

        config = Client().config()
        client = Mock()
        client.config.return_value = config
        client.get_cloudfront.return_value = cloudfront
        MockClient.return_value = client

        session = Client().session()
        transaction_id = TaskTransaction.new_id()
        image = Image(filename='abad1dea')
        image.created_at = '2001-01-01 00:00:00'
        session.add(image)
        session.flush()

        invalidate = NeverCalledDirectlyInvalidate()
        invalidate.retry = Mock()
        invalidate(transaction_id, image.image_id)

        invalidate.retry.assert_called_with(exc=error)

    @raises(CloudFrontServerError)
    @with_settings(aws={'cloudfront_distribution_id': 'SHEESHJESSICA'})
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

        transaction_id = TaskTransaction.new_id()
        session = Client().session()
        image = Image(filename='abad1dea')
        image.created_at = '2001-01-01 00:00:00'
        session.add(image)
        session.flush()

        Invalidate()(transaction_id, image.image_id)

    @with_settings(aws={'cloudfront_distribution_id': 'JEEZAMANDA'})
    def test_invalidate_an_image(self):
        cloudfront = Mock()
        Client().get_cloudfront = Mock()
        Client().get_cloudfront.return_value = cloudfront

        transaction_id = TaskTransaction.new_id()
        image = Image(filename='c1a115')
        image.created_at = '2001-05-09 13:00:00'
        session = Client().session()
        session.add(image)
        session.flush()

        Invalidate().run(transaction_id, image.image_id)

        cloudfront.create_invalidation_request.assert_called_with(
            'JEEZAMANDA', ['c1a115'])

    @with_settings(
        aws={'cloudfront_distribution_id': 'FETCHISNTGOINGTOHAPPEN'})
    def test_invalidate_an_image__with_a_resize_suffix(self):
        cloudfront = Mock()
        Client().get_cloudfront = Mock()
        Client().get_cloudfront.return_value = cloudfront

        transaction_id = TaskTransaction.new_id()
        image = Image(filename='f131d')
        image.created_at = '2001-05-09 13:00:00'
        session = Client().session()
        session.add(image)
        session.flush()

        Invalidate().run(transaction_id, image.image_id, suffix="teensy")

        cloudfront.create_invalidation_request.assert_called_with(
            'FETCHISNTGOINGTOHAPPEN', ['f131d_teensy'])

    @with_settings(cloudfront_distribution_id='SHEESHJESSICA')
    @patch('catsnap.worker.tasks.Client')
    @patch('catsnap.worker.tasks.time')
    def test_invalidation_of_new_images_is_a_noop(self, mock_time, MockClient):
        now = time.strptime('2011-05-09 15:01:01', '%Y-%m-%d %H:%M:%S')
        mock_time.strftime = time.strftime
        mock_time.gmtime.return_value = now

        get_cloudfront = Mock()
        get_cloudfront.side_effect = AssertionError('should not have called me!')
        Client().get_cloudfront = get_cloudfront

        transaction_id = TaskTransaction.new_id()
        image = Image(filename='c1a115')
        # created 1 hour before "now"
        image.created_at = '2011-05-09 13:00:00'
        session = Client().session()
        session.add(image)
        session.flush()

        Invalidate().run(transaction_id, image.image_id)

# Normally, if you call retry() from inside a task that was invoked directly
# (rather than inside an async worker), Celery will re-raise the original
# exception. This injects itself into Celery's innards so that won't happen.
class NeverCalledDirectlyInvalidate(Invalidate):
    def _get_request(self):
        request = super(NeverCalledDirectlyInvalidate, self)._get_request()
        request.called_directly = False
        return request
