from __future__ import unicode_literals

from requests.exceptions import HTTPError
from mock import patch, Mock, call
from nose.tools import eq_, raises
from tests import TestCase

from catsnap.image_truck import ImageTruck

class TestImages(TestCase):
    @patch('catsnap.image_truck.ImageTruck.calculate_filename')
    def test_save__uploads_image(self, calculate_filename):
        bucket = Mock()
        key = Mock()
        bucket.new_key.return_value = key
        calculate_filename.return_value = 'I am the keymaster'

        truck = ImageTruck('Are you the gatekeeper?', 'image/gif', None)
        truck.upload(bucket, Mock())

        bucket.new_key.assert_called_with('I am the keymaster')
        key.set_contents_from_string.assert_called_with(
                'Are you the gatekeeper?')
        key.set_metadata.assert_called_with('Content-Type', 'image/gif')
        key.make_public.assert_called_with()

    @patch('catsnap.image_truck.hashlib')
    def test_calculate_filename(self, hashlib):
        sha = Mock()
        sha.hexdigest.return_value = 'indigestible'
        hashlib.sha1.return_value = sha
        truck = ImageTruck('razors', None, None)
        eq_(truck.calculate_filename(), 'indigestible')
        hashlib.sha1.assert_called_with('razors')

    @patch('catsnap.image_truck.requests')
    def test_new_from_url(self, requests):
        response = Mock()
        response.content = "Ain't no party like a Liz Lemon party"
        response.headers = {'content-type': 'party'}
        requests.get.return_value = response

        truck = ImageTruck.new_from_url('http://some.url')
        eq_(truck.contents, "Ain't no party like a Liz Lemon party")
        eq_(truck.content_type, "party")
        eq_(truck.source_url, "http://some.url")

    @raises(HTTPError)
    @patch('catsnap.image_truck.requests')
    def test_new_from_url__raises_on_non_200(self, requests):
        response = Mock()
        response.raise_for_status.side_effect = HTTPError
        requests.get.return_value = response

        ImageTruck.new_from_url('http://some.url')

    @patch('catsnap.image_truck.ImageTruck.calculate_filename')
    def test_url(self, calculate_filename):
        calculate_filename.return_value = 'greensleeves'
        bucket = Mock()
        bucket.name = 'tune-carrier'

        truck = ImageTruck('greensleeves', None, None)
        eq_(truck.url(bucket),
                'https://s3.amazonaws.com/tune-carrier/greensleeves')

    def test_url_for_filename(self):
        bucket = Mock()
        bucket.name = 'greeble'
        eq_(ImageTruck.url_for_filename('CAFEBABE', bucket),
                'https://s3.amazonaws.com/greeble/CAFEBABE')
