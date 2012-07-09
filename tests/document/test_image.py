from __future__ import unicode_literals

from mock import patch, Mock, MagicMock
from nose.tools import eq_
from boto.dynamodb.exceptions import DynamoDBKeyNotFoundError

from catsnap.document.image import Image

class TestAddTags():
    def test_sends_to_dynamo(self):
        item = MagicMock()
        table = Mock()
        table.get_item.side_effect = DynamoDBKeyNotFoundError('no such image')
        table.new_item.return_value = item
        image = Image('deadbeef', 'mlkshk.com/kitty')
        image._stored_table = table

        image.add_tags(['cat', 'kitten'])
        table.new_item.assert_called_with(hash_key='deadbeef', attrs = {
            'tags': [ 'cat', 'kitten' ],
            'source_url': 'mlkshk.com/kitty'})
        item.put.assert_called_with()

    def test_appends_tags_to_existing_image(self):
        table = Mock()
        item = MagicMock()
        item.__getitem__.return_value = ['cat']
        table.get_item.return_value = item

        image = Image('BABB1E5')
        image._stored_table = table
        image.add_tags(['kitten'])

        eq_(table.new_item.call_count, 0, "shouldn't've made a new entry")
        item.__setitem__.assert_called_with('tags', ['cat', 'kitten'])
        item.put.assert_called_with()

    def test_overwrites_source_url_if_present(self):
        table = Mock()
        item = MagicMock()
        def getitem(key):
            if key == 'tags':
                return [ 'cat' ]
            elif key == 'source_url':
                return 'http://mlkshk.com'
            else:
                raise KeyError(key)
        item.__getitem__.side_effect = getitem
        table.get_item.return_value = item
        image_with_url = Image('BABB1E5', 'http://imgur.com')
        image_with_url._stored_table = table

        image_with_url.add_tags(['kitten'])
        item.__setitem__.assert_called_with('source_url', 'http://imgur.com')

