from __future__ import unicode_literals

from catsnap import Config, HASH_KEY
from boto.dynamodb.batch import BatchWriteList, BatchList
from boto.dynamodb.item import Item
import json

def get_tag_items(tag_names):
    if not tag_names:
        raise StopIteration

    dynamo = Config().get_dynamodb()
    table = Config().table('tag')
    batch_list = BatchList(dynamo)
    batch_list.add_batch(table, tag_names,
            attributes_to_get=['filenames', HASH_KEY])
    response = dynamo.batch_get_item(batch_list)
    items = response['Responses'][table.name]['Items']
    unprocessed_keys = []
    if response['UnprocessedKeys'] \
            and table.name in response['UnprocessedKeys']:
        for key in response['UnprocessedKeys'][table.name]['Keys']:
            unprocessed_keys.append(key['HashKeyElement'])

    for item in items:
        yield item
    for item in get_tag_items(unprocessed_keys):
        yield item

def get_tags(tag_names):
    for item in get_tag_items(tag_names):
        yield { 'tag': item[HASH_KEY],
                'filenames': json.loads(item['filenames'])}

