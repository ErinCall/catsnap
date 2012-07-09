from __future__ import unicode_literals

from boto.dynamodb.exceptions import DynamoDBKeyNotFoundError

from catsnap.document import Document

class Tag(Document):
    _table_name = 'tag'

    def __init__(self, name):
        self.name = name

    def add_file(self, filename):
        try:
            item = self._table().get_item(self.name)
            item['filenames'] = item['filenames'] + [filename]
        except DynamoDBKeyNotFoundError:
            item = self._table().new_item(hash_key=self.name, attrs={
                    'filenames': [ filename ]})
        item.put()

    def get_filenames(self):
        try:
            item = self._table().get_item(self.name)
        except DynamoDBKeyNotFoundError:
            return []
        return item['filenames']
