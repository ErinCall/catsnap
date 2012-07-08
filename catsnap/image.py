from __future__ import unicode_literals

import requests
import hashlib

from catsnap.tag import Tag

class Image():
    def __init__(self, contents, content_type, tags=[]):
        self.contents = contents
        self.content_type = content_type
        self._tags=tags

    @classmethod
    def new_from_url(cls, url, tags=[]):
        response = requests.get(url)
        response.raise_for_status()
        return cls(response.content, response.headers['content-type'],
                tags=tags)

    @classmethod
    def url_for_filename(cls, filename, bucket):
        return cls._url(filename, bucket.name)

    def tags(self, *args):
        if args:
            self._tags.extend(args)
        else:
            return self._tags

    def save(self, bucket, table):
        key = bucket.new_key(self.calculate_filename())
        key.set_metadata('Content-Type', self.content_type)
        key.set_contents_from_string(self.contents)
        key.make_public()

        filename = self.calculate_filename()
        for tag in self._tags:
            Tag(tag).save(table, filename)

    def calculate_filename(self):
        return hashlib.sha1(self.contents).hexdigest()

    def url(self, bucket):
        return self._url(self.calculate_filename(), bucket.name)

    @classmethod
    def _url(cls, filename, bucket_name):
        return 'https://s3.amazonaws.com/%(bucket)s/%(filename)s' % {
                'bucket': bucket_name, 'filename': filename}
