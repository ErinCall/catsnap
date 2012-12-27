from __future__ import unicode_literals
from catsnap import Client, HASH_KEY
from boto.dynamodb.batch import BatchList

MAX_ITEMS_TO_REQUEST = 99

def get_item_batch(tag_names, table_name, attributes_to_get):
    if not tag_names:
        raise StopIteration

    tag_names = list(set(tag_names))

    unprocessed_keys = tag_names[MAX_ITEMS_TO_REQUEST:]
    tag_names = tag_names[:MAX_ITEMS_TO_REQUEST]

    dynamo = Client().get_dynamodb()
    table = Client().table(table_name)
    batch_list = BatchList(dynamo)
    batch_list.add_batch(table, tag_names,
            attributes_to_get=attributes_to_get + [HASH_KEY])
    response = dynamo.batch_get_item(batch_list)
    items = response['Responses'][table.name]['Items']
    if response['UnprocessedKeys'] \
            and table.name in response['UnprocessedKeys']:
        for key in response['UnprocessedKeys'][table.name]['Keys']:
            unprocessed_keys.append(key['HashKeyElement'])

    for item in items:
        yield item
    for item in get_item_batch(unprocessed_keys, table_name, attributes_to_get):
        yield item

