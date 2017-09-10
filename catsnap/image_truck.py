#It's a big truck. You can just dump stuff on it.

import requests
from requests.exceptions import SSLError
import hashlib
import subprocess
import tempfile
import os
import re

from catsnap import Client

class ImageTruck():
    def __init__(self, contents, content_type, source_url):
        self.contents = contents
        self.content_type = content_type
        self.source_url = source_url
        self.filename = self.calculate_filename()

    @classmethod
    def new_from_url(cls, url):
        try:
            response = requests.get(url)
        except SSLError as e:
            if 'sslv3 alert handshake failure' in str(e):
                raise TryHTTPError(url)
            else:
                raise
        response.raise_for_status()
        return cls(response.content, response.headers['content-type'],
                url)

    @classmethod
    def new_from_file(cls, filename):
        with open(filename, 'br') as image_file:
            contents = image_file.read()
        file_info = subprocess.check_output(['file', filename])
        match = re.search(r'(\w+) image data', file_info.decode('utf-8'))
        if not match:
            raise TypeError("'%s' doesn't seem to be an image file" % filename)
        filetype = match.groups()[0].lower()

        return cls(contents, 'image/'+filetype, None)

    @classmethod
    def new_from_stream(cls, stream):
        (_, image_file) = tempfile.mkstemp()
        with open(image_file, 'bw') as fh:
            fh.write(stream.read())
        try:
            return cls.new_from_file(image_file)
        finally:
            os.unlink(image_file)

    @classmethod
    def new_from_image(cls, image):
        (_, image_file) = tempfile.mkstemp()
        key = Client().bucket().get_key(image.filename)
        if key is None:
            raise KeyError(image.filename)

        key.get_contents_to_filename(image_file)

        try:
            return cls.new_from_file(image_file)
        finally:
            os.unlink(image_file)

    @classmethod
    def new_from_something(cls, path):
        url = requests.utils.urlparse(path)
        if url.scheme:
            return cls.new_from_url(path)
        else:
            return cls.new_from_file(path)

    @classmethod
    def url_for_filename(cls, filename):
        return cls._url(filename)

    def upload(self):
        self._upload(self.filename, self.contents)

    def upload_resize(self, resized_contents, suffix):
        filename = '%s_%s' % (self.filename, suffix)
        self._upload(filename, resized_contents)

    def _upload(self, filename, contents):
        key = Client().bucket().new_key(filename)
        key.set_metadata('Content-Type', self.content_type)
        key.set_contents_from_string(contents)
        key.make_public()

    def calculate_filename(self):
        return hashlib.sha1(self.contents).hexdigest()

    def url(self, **kwargs):
        return self._url(self.filename)

    @classmethod
    def _url(cls, filename):
        config = Client().config()
        if 'aws.cloudfront_distribution_id' in config:
            distro_id = config['aws.cloudfront_distribution_id']
            cloudfront_url = Client().cloudfront_url(distro_id)
            url = 'https://%(host)s/%(filename)s' % {
                    'host': cloudfront_url, 'filename': filename}
        else:
            url = 'https://s3.amazonaws.com/%(bucket)s/%(filename)s' % {
                    'bucket': config['aws.bucket'], 'filename': filename}
        return cls.extensioned(url)

    @classmethod
    def extensioned(cls, url):
        config = Client().config()
        if 'extension' in config and config['extension']:
            url += '#.gif'
        return url

    @classmethod
    def contents_of_filename(cls, filename):
        key = Client().bucket().get_key(filename)
        if key is None:
            raise KeyError(filename)
        return key.get_contents_as_string()

class TryHTTPError(Exception):
    pass
