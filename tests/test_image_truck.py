import io
import tempfile
import ssl
import urllib3.exceptions
from urllib3.packages.ssl_match_hostname import CertificateError
import requests.exceptions
from mock import patch, MagicMock, Mock
from nose.tools import eq_, raises
from tests import TestCase, with_settings
from tests.image_helper import SMALL_JPG

from catsnap import Client
from catsnap.table.image import Image
from catsnap.image_truck import ImageTruck, TryHTTPError

class TestImageTruck(TestCase):
    @patch('catsnap.image_truck.Client')
    @patch('catsnap.image_truck.ImageTruck.calculate_filename')
    def test_save__uploads_image(self, calculate_filename, MockClient):
        bucket = Mock()
        key = Mock()
        bucket.new_key.return_value = key
        client = Mock()
        client.bucket.return_value = bucket
        client.config = MagicMock()
        MockClient.return_value = client
        calculate_filename.return_value = 'I am the keymaster'

        truck = ImageTruck('Are you the gatekeeper?', 'image/gif', None)
        truck.upload()

        bucket.new_key.assert_called_with('I am the keymaster')
        key.set_contents_from_string.assert_called_with(
                'Are you the gatekeeper?')
        key.set_metadata.assert_called_with('Content-Type', 'image/gif')
        key.make_public.assert_called_with()

    @patch('catsnap.image_truck.Client')
    @patch('catsnap.image_truck.ImageTruck.calculate_filename')
    def test_upload_resize(self, calculate_filename, MockClient):
        bucket = Mock()
        key = Mock()
        bucket.new_key.return_value = key
        client = Mock()
        client.config.return_value = MagicMock()
        client.bucket.return_value = bucket
        MockClient.return_value = client
        calculate_filename.return_value = 'faceb00c'

        truck = ImageTruck('contentsoffile', 'image/gif', None)
        truck.upload_resize('resizedcontents', 'small')

        bucket.new_key.assert_called_with('faceb00c_small')
        key.set_contents_from_string.assert_called_with('resizedcontents')
        key.set_metadata.assert_called_with('Content-Type', 'image/gif')
        key.make_public.assert_called_once()

    @patch('catsnap.image_truck.hashlib')
    def test_calculate_filename(self, hashlib):
        sha = Mock()
        sha.hexdigest.return_value = 'indigestible'
        hashlib.sha1.return_value = sha
        truck = ImageTruck('razors', None, None)
        eq_(truck.calculate_filename(), 'indigestible')
        hashlib.sha1.assert_called_with('razors')

    @patch('catsnap.image_truck.hashlib')
    def test_filename_is_calculated_on_initialization(self, hashlib):
        sha = Mock()
        sha.hexdigest.return_value = 'indigestible'
        hashlib.sha1.return_value = sha
        truck = ImageTruck('razors', None, None)
        eq_(truck.filename, 'indigestible')

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

    @raises(requests.exceptions.HTTPError)
    @patch('catsnap.image_truck.requests')
    def test_new_from_url__raises_on_non_200(self, mock_requests):
        response = Mock()
        response.raise_for_status.side_effect = requests.exceptions.HTTPError
        mock_requests.get.return_value = response

        ImageTruck.new_from_url('http://some.url')

    @raises(TryHTTPError)
    @patch('catsnap.image_truck.requests')
    def test_new_from_url_raises_usefully_for_sni_trouble(self, mock_requests):
        error = requests.exceptions.SSLError(
            urllib3.exceptions.SSLError(
                ssl.SSLError(1, '_ssl.c:503: error:14077410:SSL routines:'
                                'SSL23_GET_SERVER_HELLO:sslv3 alert handshake '
                                'failure')))

        mock_requests.get.side_effect = error

        ImageTruck.new_from_url('https://some.server.using.sni/image.jpg')

    @raises(requests.exceptions.SSLError)
    @patch('catsnap.image_truck.requests')
    def test_new_from_url_reraises_non_sni_ssl_errors(self, mock_requests):
        error = requests.exceptions.SSLError(
            urllib3.exceptions.SSLError(
                CertificateError("hostname 'catsinthecity.com' doesn't "
                                 "match 'nossl.edgecastcdn.net'")))

        mock_requests.get.side_effect = error

        ImageTruck.new_from_url('https://catsinthecity.com/image.jpg')

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
            ImageTruck.new_from_file(__file__)
        except Exception as e:
            eq_(e.message, "'%s' doesn't seem to be an image file" % __file__)
            eq_(type(e), TypeError)
        else:
            raise AssertionError('expected an error')

    def test_new_from_stream(self):
        with open(SMALL_JPG, 'r') as stream:
            truck = ImageTruck.new_from_stream(stream)
            eq_(truck.content_type, 'image/jpeg')
            stream.seek(0)
            eq_(truck.contents, stream.read())

    @patch('catsnap.image_truck.Client')
    @patch('catsnap.image_truck.subprocess')
    def test_new_from_image(self, subprocess, MockClient):
        subprocess.check_output.return_value = \
                'space-centurion.png: PNG image data, 1280 x 800, ' \
                '8-bit/color RGB, non-interlaced'

        def get_contents_to_filename(filename):
            with open(filename, 'w') as fh:
                fh.write('brain, skull, etc')
        key = Mock()
        key.get_contents_to_filename.side_effect = get_contents_to_filename
        bucket = Mock()
        bucket.get_key.return_value = key
        client = Mock()
        client.bucket.return_value = bucket
        MockClient.return_value = client

        image = Image(filename='faceface')
        truck = ImageTruck.new_from_image(image)
        eq_(truck.contents, 'brain, skull, etc')

        bucket.get_key.assert_called_with('faceface')

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

    @with_settings(aws={'bucket': 'tune-carrier'}, extension=False)
    @patch('catsnap.image_truck.ImageTruck.calculate_filename')
    def test_url(self, calculate_filename):
        calculate_filename.return_value = 'greensleeves'

        truck = ImageTruck('greensleeves', None, None)
        eq_(truck.url(), 'https://s3.amazonaws.com/tune-carrier/greensleeves')

    @patch('catsnap.image_truck.Client')
    @patch('catsnap.image_truck.ImageTruck.calculate_filename')
    @with_settings(aws={'cloudfront_distribution_id': 'JEEZAMANDA'})
    def test_url__with_cloudfront_url(self, calculate_filename, MockClient):
        client = Mock()
        client.cloudfront_url.return_value = \
            'ggaaghlhaagl.cloudfront.net'
        client.config.return_value = Client().config()
        MockClient.return_value = client

        calculate_filename.return_value = 'chumbawamba'
        truck = ImageTruck('tubthumper', None, None)

        url = truck.url()
        eq_(url, 'https://ggaaghlhaagl.cloudfront.net/chumbawamba')
        client.cloudfront_url.assert_called_with('JEEZAMANDA')

    @with_settings(aws={'bucket': 'tune'}, extension=True)
    @patch('catsnap.image_truck.ImageTruck.calculate_filename')
    def test_url__with_extension(self, calculate_filename):
        calculate_filename.return_value = 'greensleeves'
        truck = ImageTruck('greensleeves', None, None)

        url = truck.url()
        eq_(url, 'https://s3.amazonaws.com/tune/greensleeves#.gif')

    @with_settings(aws={'bucket': 'greeble'}, extension=False)
    def test_url_for_filename(self):
        eq_(ImageTruck.url_for_filename('CAFEBABE'),
                'https://s3.amazonaws.com/greeble/CAFEBABE')

    @with_settings(extension=True)
    def test_extensioned_url(self):
        image_path = ImageTruck.extensioned('example.com/image')
        eq_(image_path, 'example.com/image#.gif')

    @with_settings(aws={'bucket': 'tuneholder'})
    def test_calculate_url(self):
        url = ImageTruck._url('deadbeef')
        eq_(url, 'https://s3.amazonaws.com/tuneholder/deadbeef')

    @with_settings(extension=True, aws={'bucket': 'tuneholder'})
    def test_calculate_url__with_extension(self):
        url = ImageTruck._url('deadbeef')
        eq_(url, 'https://s3.amazonaws.com/tuneholder/deadbeef#.gif')

    @patch('catsnap.image_truck.Client')
    def test_get_contents_of_filename(self, MockClient):
        key = Mock()
        key.get_contents_as_string.return_value = 'cow innards'
        bucket = Mock()
        bucket.get_key.return_value = key
        client = Mock()
        client.bucket.return_value = bucket
        MockClient.return_value = client

        contents = ImageTruck.contents_of_filename('deadbeef')
        eq_(contents, 'cow innards')

        bucket.get_key.assert_called_with('deadbeef')

    @raises(KeyError)
    @patch('catsnap.image_truck.Client')
    def test_get_contents_of_nonexistent_filename(self, MockClient):
        bucket = Mock()
        bucket.get_key.return_value = None
        client = Mock()
        client.bucket.return_value = bucket
        MockClient.return_value = client

        ImageTruck.contents_of_filename('x')

