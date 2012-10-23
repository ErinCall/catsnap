from __future__ import unicode_literals

from catsnap import HASH_KEY
from catsnap.batch import get_item_batch
import json

def get_images(filenames):
    for item in get_item_batch(filenames, 'image', ['tags']):
        yield {'filename': item[HASH_KEY],
               'tags': json.loads(item['tags'])}
