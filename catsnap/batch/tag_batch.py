from __future__ import unicode_literals

from catsnap import Config, HASH_KEY
from boto.dynamodb.batch import BatchList
import json

def get_tags(tag_names):
    if not tag_names:
        raise StopIteration
    dynamo = Config().get_dynamodb()
    table = Config().table('tag')
    batch_list = BatchList(dynamo)
    batch_list.add_batch(table, tag_names,
            attributes_to_get=['filenames', HASH_KEY])
    response = dynamo.batch_get_item(batch_list)
    items = response['Responses'][table.name]['Items']
    for item in items:
        item['tag'] = item.pop(HASH_KEY)
        item['filenames'] = json.loads(item['filenames'])
    unprocessed_keys = []
    if response['UnprocessedKeys'] \
            and table.name in response['UnprocessedKeys']:
        for key in response['UnprocessedKeys'][table.name]['Keys']:
            unprocessed_keys.append(key['HashKeyElement'])

    for item in items:
        yield item
    if not unprocessed_keys:
        raise StopIteration
    for item in get_tags(unprocessed_keys):
        yield item
