from __future__ import unicode_literals

from catsnap import Client, HASH_KEY
from boto.dynamodb.batch import BatchWriteList, BatchList
from boto.dynamodb.item import Item
from catsnap.batch import get_item_batch
import json

def get_tags(tag_names):
    for item in get_item_batch(tag_names, 'tag', ['filenames']):
        yield { 'tag': item[HASH_KEY],
                'filenames': json.loads(item['filenames'])}

def add_image_to_tags(filename, tag_names):
    items = list(get_item_batch(tag_names, 'tag', ['filenames']))
    for item in items:
        filenames = json.loads(item['filenames'])
        filenames.append(filename)
        item['filenames'] = json.dumps(filenames)

    table = Client().table('tag')
    for new_tag in set(tag_names) - set(x[HASH_KEY] for x in items):
        items.append(table.new_item(hash_key = new_tag,
                attrs={'filenames': json.dumps([filename])}))

    _submit_items(table, items)

def _submit_items(table, items):
    dynamo = Client().get_dynamodb()
    write_list = BatchWriteList(dynamo)
    write_list.add_batch(table, puts=items)
    response = write_list.submit()
    if 'UnprocessedItems' in response \
            and table.name in response['UnprocessedItems']:
        unprocessed_keys = set(x['PutRequest']['Item'][HASH_KEY]
                for x in response['UnprocessedItems'][table.name])
        unprocessed_items = filter(
                lambda x: x[HASH_KEY] in unprocessed_keys, items)
        _submit_items(table, unprocessed_items)
