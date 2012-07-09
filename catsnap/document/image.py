from __future__ import unicode_literals

from boto.dynamodb.exceptions import DynamoDBKeyNotFoundError

from catsnap.document import Document

class Image(Document):
    _table_name = 'image'

    def __init__(self, filename, source_url=None):
        self.filename = filename
        self.source_url = source_url

    def add_tags(self, tags):
        try:
            item = self._table().get_item(self.filename)
            item['tags'] = item['tags'] + tags
        except DynamoDBKeyNotFoundError:
            item = self._table().new_item(hash_key=self.filename, attrs={
                'tags': tags,
                'source_url': self.source_url})
        if self.source_url is not None:
            item['source_url'] = self.source_url
        item.put()

    def get_tags(self):
        try:
            item = self._table().get_item(self.filename)
        except DynamoDBKeyNotFoundError:
            return []
        return item['tags']

    def get_source_url(self):
        try:
            item = self._table().get_item(self.filename)
        except DynamoDBKeyNotFoundError:
            return None
        return item['source_url']
