from __future__ import print_function, unicode_literals

from requests.exceptions import HTTPError
from mock import patch, Mock
from nose.tools import eq_, raises

from catsnap import load_image

class TestImageLoading():
    @patch('catsnap.load_image.requests')
    def test_load_url(self, requests):
        response = Mock()
        response.content = "Ain't no party like a Liz Lemon party"
        requests.get.return_value = response

        image_contents = load_image.load_image('http://some.url')
        eq_(image_contents, "Ain't no party like a Liz Lemon party")

    @raises(HTTPError)
    @patch('catsnap.load_image.requests')
    def test_load_url__raises_on_non_200(self, requests):
        response = Mock()
        response.raise_for_status.side_effect = HTTPError
        requests.get.return_value = response

        load_image.load_image('http://some.url')
