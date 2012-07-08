from __future__ import unicode_literals

from requests.exceptions import HTTPError
from mock import patch, Mock
from nose.tools import eq_, raises

from catsnap.image import Image

class TestImages():
    @patch('catsnap.image.Image.calculate_filename')
    def test_save(self, calculate_filename):
        bucket = Mock()
        key = Mock()
        bucket.new_key.return_value = key
        calculate_filename.return_value = 'I am the keymaster'

        image = Image('Are you the gatekeeper?', 'image/gif')
        image.save(bucket)

        bucket.new_key.assert_called_with('I am the keymaster')
        key.set_contents_from_string.assert_called_with(
                'Are you the gatekeeper?')
        key.set_metadata.assert_called_with('Content-Type', 'image/gif')
        key.make_public.assert_called()

    @patch('catsnap.image.hashlib')
    def test_calculate_filename(self, hashlib):
        sha = Mock()
        sha.hexdigest.return_value = 'indigestible'
        hashlib.sha1.return_value = sha
        image = Image('razors', None)
        eq_(image.calculate_filename(), 'indigestible')
        hashlib.sha1.assert_called_with('razors')

    @patch('catsnap.image.requests')
    def test_new_from_url(self, requests):
        response = Mock()
        response.content = "Ain't no party like a Liz Lemon party"
        response.headers = {'content-type': 'party'}
        requests.get.return_value = response

        image = Image.new_from_url('http://some.url')
        eq_(image.contents, "Ain't no party like a Liz Lemon party")

    @raises(HTTPError)
    @patch('catsnap.image.requests')
    def test_new_from_url__raises_on_non_200(self, requests):
        response = Mock()
        response.raise_for_status.side_effect = HTTPError
        requests.get.return_value = response

        Image.new_from_url('http://some.url')

    @patch('catsnap.image.Image.calculate_filename')
    def test_url(self, calculate_filename):
        calculate_filename.return_value = 'greensleeves'
        bucket = Mock()
        bucket.name = 'tune-carrier'

        image = Image('greensleeves', None)
        eq_(image.url(bucket),
                'https://s3.amazonaws.com/tune-carrier/greensleeves')
