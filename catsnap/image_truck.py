from __future__ import unicode_literals

#It's a big truck. You can just dump stuff on it.

import requests
import hashlib
import subprocess
import re

from catsnap import Client

class ImageTruck():
    def __init__(self, contents, content_type, source_url, suffix=None):
        self.contents = contents
        self.content_type = content_type
        self.source_url = source_url
        self.suffix = suffix

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
    def new_from_stream(cls, stream, content_type, suffix=None):
        contents = stream.read()
        return cls(contents, content_type, None, suffix=suffix)

    @classmethod
    def new_from_something(cls, path):
        url = requests.utils.urlparse(path)
        if url.scheme:
            return cls.new_from_url(path)
        else:
            return cls.new_from_file(path)

    @classmethod
    def url_for_filename(cls, filename):
        return cls._url(filename, Client().config().bucket)

    def upload(self):
        key = Client().bucket().new_key(self.calculate_filename())
        key.set_metadata('Content-Type', self.content_type)
        key.set_contents_from_string(self.contents)
        key.make_public()

        filename = self.calculate_filename()

    def calculate_filename(self):
        raw_filename = hashlib.sha1(self.contents).hexdigest()
        if self.suffix is None:
            return raw_filename
        return '%s_%s' % (raw_filename, self.suffix)

    def url(self, **kwargs):
        return self._url(self.calculate_filename(), Client().config().bucket)

    @classmethod
    def _url(cls, filename, bucket_name):
        url = 'https://s3.amazonaws.com/%(bucket)s/%(filename)s' % {
                'bucket': bucket_name, 'filename': filename}
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
