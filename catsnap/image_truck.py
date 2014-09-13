from __future__ import unicode_literals

#It's a big truck. You can just dump stuff on it.

import requests
import hashlib
import subprocess
import re

from catsnap import Client

class ImageTruck():
    def __init__(self, contents, content_type, source_url):
        self.contents = contents
        self.content_type = content_type
        self.source_url = source_url

    @classmethod
    def new_from_url(cls, url):
        response = requests.get(url)
        response.raise_for_status()
        return cls(response.content, response.headers['content-type'],
                url)

    @classmethod
    def new_from_file(cls, filename):
        with open(filename, 'r') as image_file:
            contents = image_file.read()
        file_info = subprocess.check_output(['file', filename])
        match = re.search(r'(\w+) image data', file_info)
        if not match:
            raise TypeError("'%s' doesn't seem to be an image file" % filename)
        filetype = match.groups()[0].lower()

        return cls(contents, 'image/'+filetype, None)

    @classmethod
    def new_from_stream(cls, stream, content_type):
        contents = stream.read()
        return cls(contents, content_type, None)

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
        key = Client().bucket().new_key(self.calculate_filename())
        key.set_metadata('Content-Type', self.content_type)
        key.set_contents_from_string(self.contents)
        key.make_public()

    def upload_resize(self, resized_contents, suffix):
        filename = '%s_%s' % (self.calculate_filename(), suffix)
        key = Client().bucket().new_key(filename)
        key.set_metadata('Content-Type', self.content_type)
        key.set_contents_from_string(resized_contents)
        key.make_public()

        config = Client().config()
        if 'cloudfront_distribution_id' in config:
            distro_id = config['cloudfront_distribution_id']
            Client().get_cloudfront().create_invalidation_request(
                distro_id, filename)

    def calculate_filename(self):
        return hashlib.sha1(self.contents).hexdigest()

    def url(self, **kwargs):
        return self._url(self.calculate_filename())

    @classmethod
    def _url(cls, filename):
        config = Client().config()
        if 'cloudfront_distribution_id' in config:
            distro_id = config['cloudfront_distribution_id']
            cloudfront_url = Client().cloudfront_url(distro_id)
            url = '%(host)s/%(filename)s' % {
                    'host': cloudfront_url, 'filename': filename}
        else:
            url = 'https://s3.amazonaws.com/%(bucket)s/%(filename)s' % {
                    'bucket': config.bucket, 'filename': filename}
        return cls.extensioned(url)

    @classmethod
    def extensioned(cls, url):
        if Client().config().extension:
            url += '#.gif'
        return url

    @classmethod
    def contents_of_filename(cls, filename):
        key = Client().bucket().get_key(filename)
        if key is None:
            raise KeyError(filename)
        return key.get_contents_as_string()
