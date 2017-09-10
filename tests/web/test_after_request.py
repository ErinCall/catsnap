from contextlib import contextmanager
from redis.exceptions import ConnectionError
from tests import TestCase
from nose.tools import eq_
from mock import Mock, patch
import sqlalchemy.exc
from catsnap import Client
from catsnap.web import app
from catsnap.web.formatted_routes import formatted_route, abort
from catsnap.db_redis_coordination import delay
from catsnap.table.album import Album

class TestAfterRequestHandler(TestCase):
    @patch('catsnap.web.coordinated_rollback')
    def test_unsuccessful_responses_trigger_rollbacks(self, mock_rollback):
        session = Client().session()

        with erroring_route():
            response = self.app.get('/trigger_for_test')
        eq_(response.status_code, 500)

        mock_rollback.assert_called_with([])

@contextmanager
def erroring_route():
    try:
        @formatted_route('/trigger_for_test')
        def trigger_for_test(request_format):
            abort(request_format, 500, "No Mr. Bond, I expect you to die.")

        yield
    finally:
        del(app.url_map._rules_by_endpoint['trigger_for_test'])
