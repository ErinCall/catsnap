from __future__ import unicode_literals

import json
from boto.dynamodb.exceptions import DynamoDBKeyNotFoundError

from catsnap.ordered_set import OrderedSet
from catsnap.document import Document

class Tag(Document):
    _table_name = 'tag'

    def __init__(self, name):
        self.name = name

    def add_file(self, filename):
        existing_filenames = []
        try:
            item = self._table().get_item(self.name)
            existing_filenames = json.loads(item['filenames'])
        except DynamoDBKeyNotFoundError:
            item = self._table().new_item(hash_key=self.name, attrs={})

        item['filenames'] = json.dumps(list(OrderedSet(existing_filenames +
                                                       [filename])))
        item.put()

    def get_filenames(self):
        try:
            item = self._table().get_item(self.name)
        except DynamoDBKeyNotFoundError:
            return []
        return json.loads(item['filenames'])
