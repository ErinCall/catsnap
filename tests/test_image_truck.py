from __future__ import unicode_literals

import tempfile
from requests.exceptions import HTTPError
from mock import patch, Mock, call
from nose.tools import eq_, raises
from tests import TestCase

from catsnap.image_truck import ImageTruck

class TestImageTruck(TestCase):
    @patch('catsnap.image_truck.ImageTruck.calculate_filename')
    def test_save__uploads_image(self, calculate_filename):
        bucket = Mock()
        key = Mock()
        bucket.new_key.return_value = key
        calculate_filename.return_value = 'I am the keymaster'

        truck = ImageTruck('Are you the gatekeeper?', 'image/gif', None)
        truck._stored_bucket = bucket
        truck.upload()

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

    @patch('catsnap.image_truck.subprocess')
    def test_new_from_file(self, subprocess):
        subprocess.check_output.return_value = \
                'space-centurion.png: PNG image data, 1280 x 800, ' \
                '8-bit/color RGB, non-interlaced'
        (_, image) = tempfile.mkstemp()
        with open(image, 'w') as image_file:
            image_file.write('here are some contents')

        truck = ImageTruck.new_from_file(image)
        eq_(truck.content_type, "image/png")
        eq_(truck.contents, 'here are some contents')
        eq_(truck.source_url, None)
        subprocess.check_output.assert_called_with(['file', image])

    def test_new_from_file__raises_well_for_non_image_files(self):
        try:
            truck = ImageTruck.new_from_file(__file__)
        except Exception, e:
            eq_(e.message, "'%s' doesn't seem to be an image file" % __file__)
            eq_(type(e), TypeError)
        else:
            raise AssertionError('expected an error')

    @patch('catsnap.image_truck.ImageTruck.new_from_url')
    @patch('catsnap.image_truck.ImageTruck.new_from_file')
    def test_new_from_something__delegates_to_new_from_url(self,
            new_from_file, new_from_url):
        new_from_file.side_effect = AssertionError('not supposed to be here')

        ImageTruck.new_from_something('http://facebook.com')
        new_from_url.assert_called_with('http://facebook.com')

    @patch('catsnap.image_truck.ImageTruck.new_from_url')
    @patch('catsnap.image_truck.ImageTruck.new_from_file')
    def test_new_from_something__delegates_to_new_from_file(self,
            new_from_file, new_from_url):
        new_from_url.side_effect = AssertionError('not supposed to be here')

        ImageTruck.new_from_something('/Users/andrewlorente/.bashrc')
        new_from_file.assert_called_with('/Users/andrewlorente/.bashrc')

    @patch('catsnap.image_truck.Config')
    @patch('catsnap.image_truck.ImageTruck.calculate_filename')
    def test_url(self, calculate_filename, Config):
        config = Mock()
        config.bucket_name.return_value = 'tune-carrier'
        Config.return_value = config
        calculate_filename.return_value = 'greensleeves'

        truck = ImageTruck('greensleeves', None, None)
        eq_(truck.url(), 'https://s3.amazonaws.com/tune-carrier/greensleeves')

    @patch('catsnap.image_truck.ImageTruck._url')
    @patch('catsnap.image_truck.Config')
    @patch('catsnap.image_truck.ImageTruck.calculate_filename')
    def test_url__with_extension(self, calculate_filename, Config, _url):
        config = Mock()
        config.bucket_name.return_value = 'tune-carrier'
        Config.return_value = config
        calculate_filename.return_value = 'greensleeves'
        truck = ImageTruck('greensleeves', None, None)

        truck.url(extension=True)
        _url.assert_called_once_with('greensleeves', 'tune-carrier',
                extension=True)

    @patch('catsnap.image_truck.Config')
    def test_url_for_filename(self, Config):
        config = Mock()
        config.bucket_name.return_value = 'greeble'
        Config.return_value = config
        eq_(ImageTruck.url_for_filename('CAFEBABE'),
                'https://s3.amazonaws.com/greeble/CAFEBABE')

    @patch('catsnap.image_truck.Config')
    @patch('catsnap.image_truck.ImageTruck._url')
    def test_url_for_filename__with_extension(self, _url, Config):
        config = Mock()
        config.bucket_name.return_value = 'greeble'
        Config.return_value = config

        ImageTruck.url_for_filename('CAFEBABE', extension=True)
        _url.assert_called_once_with('CAFEBABE', 'greeble', extension=True)

    def test_calculate_url(self):
        url = ImageTruck._url('deadbeef', 'tuneholder')
        eq_(url, 'https://s3.amazonaws.com/tuneholder/deadbeef')

    def test_calculate_url__with_extension(self):
        url = ImageTruck._url('deadbeef', 'tuneholder', extension=True)
        eq_(url, 'https://s3.amazonaws.com/tuneholder/deadbeef#.gif')

    @patch('catsnap.image_truck.Config')
    def test_get_bucket_creates_bucket_connection(self, Config):
        config = Mock()
        Config.return_value = config
        mock_bucket = Mock()
        config.bucket.return_value = mock_bucket

        truck = ImageTruck(None, None, None)
        bucket = truck._bucket()
        eq_(bucket, mock_bucket)
        eq_(truck._stored_bucket, mock_bucket)
        config.bucket.assert_called_with()

    @patch('catsnap.image_truck.Config')
    def test_get_bucket_creates_bucket_connection(self, Config):
        config = Mock()
        Config.return_value = config
        mock_bucket = Mock()
        truck = ImageTruck(None, None, None)
        truck._stored_bucket = mock_bucket

        bucket = truck._bucket()
        eq_(bucket, mock_bucket)
        eq_(config.table.call_count, 0)
