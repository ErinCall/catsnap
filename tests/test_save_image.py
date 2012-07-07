from __future__ import unicode_literals

from mock import patch, Mock
from nose.tools import eq_, raises

from catsnap import save_image

class TestImageSaving():
    @patch('catsnap.save_image.key_for_image')
    def test_save_image(self, key_for_image):
        bucket = Mock()
        key = Mock()
        bucket.new_key.return_value = key
        key_for_image.return_value = 'I am the keymaster'

        save_image.save_image(bucket, 'Are you the gatekeeper?', 'image/gif')
        bucket.new_key.assert_called_with('I am the keymaster')
        key.set_contents_from_string.assert_called_with(
                'Are you the gatekeeper?')
        key.set_metadata.assert_called_with('Content-Type', 'image/gif')
        key.make_public.assert_called()

    @patch('catsnap.save_image.hashlib')
    def test_key_for_image(self, hashlib):
        sha = Mock()
        sha.hexdigest.return_value = 'indigestible'
        hashlib.sha1.return_value = sha
        eq_(save_image.key_for_image('razors'), 'indigestible')
        hashlib.sha1.assert_called_with('razors')
