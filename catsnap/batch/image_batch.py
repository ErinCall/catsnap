from __future__ import unicode_literals

from catsnap import Client, HASH_KEY
from boto.dynamodb.batch import BatchList
import json

def get_images(filenames):
    if not filenames:
        raise StopIteration
    dynamo = Client().get_dynamodb()
    table = Client().table('image')
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

    for item in items:
        yield item
    if not unprocessed_keys:
        raise StopIteration
    for item in get_images(unprocessed_keys):
        yield item
