from __future__ import unicode_literals

from catsnap import Config, HASH_KEY
from boto.dynamodb.batch import BatchList
import json

def get_images(filenames):
    dynamo = Config().get_dynamodb()
    table = Config().table('image')
    batch_list = BatchList(dynamo)
    batch_list.add_batch(table, filenames,
            attributes_to_get=['tags', HASH_KEY])
    response = dynamo.batch_get_item(batch_list)
    items = response['Responses'][table.name]['Items']
    for item in items:
        item['filename'] = item.pop(HASH_KEY)
        item['tags'] = json.loads(item['tags'])
    unprocessed_keys = []
    if response['UnprocessedKeys'] \
            and table.name in response['UnprocessedKeys']:
        for key in response['UnprocessedKeys'][table.name]['Keys']:
            unprocessed_keys.append(key['HashKeyElement'])

    return BatchProxy(unprocessed_keys, items)

class BatchProxy(object):
    def __init__(self, unprocessed_keys, items):
        self.items = items
        self.unprocessed_keys = unprocessed_keys

    def __iter__(self):
        for item in self.items:
            yield item

        if not self.unprocessed_keys:
            raise StopIteration
        for item in get_images(self.unprocessed_keys):
            yield item

