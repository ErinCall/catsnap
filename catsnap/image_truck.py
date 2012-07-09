from __future__ import unicode_literals

#It's a big truck. You can just dump stuff on it.

import requests
import hashlib

from catsnap import Config

class ImageTruck():
    _stored_bucket = None

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

    def _bucket(self):
        self._stored_bucket = self._stored_bucket or Config().bucket()
        return self._stored_bucket

    @classmethod
    def url_for_filename(cls, filename):
        return cls._url(filename, Config().bucket().name)

    def upload(self):
        key = self._bucket().new_key(self.calculate_filename())
        key.set_metadata('Content-Type', self.content_type)
        key.set_contents_from_string(self.contents)
        key.make_public()

        filename = self.calculate_filename()

    def calculate_filename(self):
        return hashlib.sha1(self.contents).hexdigest()

    def url(self):
        return self._url(self.calculate_filename(), self._bucket().name)

    @classmethod
    def _url(cls, filename, bucket_name):
        return 'https://s3.amazonaws.com/%(bucket)s/%(filename)s' % {
                'bucket': bucket_name, 'filename': filename}
