from __future__ import unicode_literals

import requests
import hashlib

class Image():
    def __init__(self, contents, content_type, tags=[]):
        self.contents = contents
        self.content_type = content_type
        self._tags=tags

    @classmethod
    def new_from_url(cls, url):
        response = requests.get(url)
        response.raise_for_status()
        return cls(response.content, response.headers['content-type'])

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
            item = table.new_item(hash_key=tag, attrs={filename:filename})
            item.put()

    def calculate_filename(self):
        return hashlib.sha1(self.contents).hexdigest()

    def url(self, bucket):
        return 'https://s3.amazonaws.com/%(bucket)s/%(filename)s' % {
                'bucket': bucket.name, 'filename': self.calculate_filename()}
