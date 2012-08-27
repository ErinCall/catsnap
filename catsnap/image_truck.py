from __future__ import unicode_literals

#It's a big truck. You can just dump stuff on it.

import requests
import hashlib
import subprocess
import re

from catsnap import Client
from catsnap.config import MetaConfig

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
    def new_from_something(cls, path):
        url = requests.utils.urlparse(path)
        if url.scheme:
            return cls.new_from_url(path)
        else:
            return cls.new_from_file(path)

    @classmethod
    def url_for_filename(cls, filename):
        return cls._url(filename, MetaConfig().bucket,
                extension=MetaConfig().extension)

    def upload(self):
        key = Client().bucket().new_key(self.calculate_filename())
        key.set_metadata('Content-Type', self.content_type)
        key.set_contents_from_string(self.contents)
        key.make_public()

        filename = self.calculate_filename()

    def calculate_filename(self):
        return hashlib.sha1(self.contents).hexdigest()

    def url(self, **kwargs):
        return self._url(self.calculate_filename(), MetaConfig().bucket,
                extension=MetaConfig().extension)

    @classmethod
    def _url(cls, filename, bucket_name, extension=False):
        url = 'https://s3.amazonaws.com/%(bucket)s/%(filename)s' % {
                'bucket': bucket_name, 'filename': filename}
        if extension:
            url = url + '#.gif'
        return url
