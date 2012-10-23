from __future__ import unicode_literals

from catsnap import Client, HASH_KEY
from boto.dynamodb.batch import BatchList
import json

MAX_ITEMS_TO_REQUEST = 99

def get_image_items(filenames):
    if not filenames:
        raise StopIteration
    filenames = list(filenames)
    unprocessed_keys = filenames[MAX_ITEMS_TO_REQUEST:]
    filenames = filenames[:MAX_ITEMS_TO_REQUEST]

    dynamo = Client().get_dynamodb()
    table = Client().table('image')
    batch_list = BatchList(dynamo)
    batch_list.add_batch(table, filenames,
            attributes_to_get=['tags', HASH_KEY])
    response = dynamo.batch_get_item(batch_list)
    items = response['Responses'][table.name]['Items']
    if response['UnprocessedKeys'] \
            and table.name in response['UnprocessedKeys']:
        for key in response['UnprocessedKeys'][table.name]['Keys']:
            unprocessed_keys.append(key['HashKeyElement'])

    for item in items:
        yield item
    if not unprocessed_keys:
        raise StopIteration
    for item in get_image_items(unprocessed_keys):
        yield item

def get_images(filenames):
    for item in get_image_items(filenames):
        yield {'filename': item[HASH_KEY],
               'tags': json.loads(item['tags'])}
