from __future__ import unicode_literals

from boto.dynamodb.exceptions import DynamoDBKeyNotFoundError

class Tag():
    def __init__(self, name):
        self.name = name

    def save(self, table, filename):
        try:
            item = table.get_item(self.name)
            item[filename] = filename
        except DynamoDBKeyNotFoundError:
            item = table.new_item(hash_key=self.name,
                    attrs={filename: filename})
        item.put()
