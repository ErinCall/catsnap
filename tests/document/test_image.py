from __future__ import unicode_literals

from mock import patch, Mock, MagicMock, call
from nose.tools import eq_
from boto.dynamodb.exceptions import DynamoDBKeyNotFoundError
from tests import TestCase

from catsnap.document.image import Image

class TestAddTags(TestCase):
    def test_sends_to_dynamo(self):
        item = MagicMock()
        table = Mock()
        table.get_item.side_effect = DynamoDBKeyNotFoundError('no such image')
        table.new_item.return_value = item
        image = Image('deadbeef', 'mlkshk.com/kitty')
        image._stored_table = table

        image.add_tags(['cat', 'kitten'])
        table.new_item.assert_called_with(hash_key='deadbeef', attrs={})
        item.__setitem__.assert_has_calls([
                call('source_url', 'mlkshk.com/kitty'),
                call('tags', '["cat", "kitten"]')])
        item.put.assert_called_with()

    def test_appends_tags_to_existing_image(self):
        table = Mock()
        item = MagicMock()
        item.__getitem__.return_value = '["cat"]'
        table.get_item.return_value = item

        image = Image('BABB1E5')
        image._stored_table = table
        image.add_tags(['kitten'])

        eq_(table.new_item.call_count, 0, "shouldn't've made a new entry")
        item.__setitem__.assert_called_with('tags', '["cat", "kitten"]')
        item.put.assert_called_with()

    def test_appended_tags_are_unique(self):
        table = Mock()
        item = MagicMock()
        item.__getitem__.return_value = '["cat"]'
        table.get_item.return_value = item

        image = Image('BABB1E5')
        image._stored_table = table
        image.add_tags(['cat'])

        item.__setitem__.assert_called_with('tags', '["cat"]')

    def test_overwrites_source_url_if_present(self):
        table = Mock()
        item = MagicMock()
        def getitem(key):
            if key == 'tags':
                return '["cat"]'
            elif key == 'source_url':
                return 'http://mlkshk.com'
            else:
                raise KeyError(key)
        item.__getitem__.side_effect = getitem
        table.get_item.return_value = item
        image_with_url = Image('BABB1E5', 'http://imgur.com')
        image_with_url._stored_table = table

        image_with_url.add_tags(['kitten'])
        item.__setitem__.assert_has_calls([
            call('source_url', 'http://imgur.com'),
            call('tags', '["cat", "kitten"]')])

    def test_get_tags(self):
        table = Mock()
        item = MagicMock()
        item.__getitem__.return_value = '["cat", "kittycat", "dancedance"]'
        table.get_item.return_value = item
        image = Image('BADBADBADBADBAD')
        image._stored_table = table

        tags = image.get_tags()
        eq_(tags, ['cat', 'kittycat', 'dancedance'])

    def test_get_tags__returns_none_if_no_such_image(self):
        table = Mock()
        table.get_item.side_effect = DynamoDBKeyNotFoundError('no such image')
        image = Image("TH15I5N0TEVENHEX")
        image._stored_table = table

        tags = image.get_tags()
        eq_(tags, [])

    def test_get_source_url(self):
        table = Mock()
        item = MagicMock()
        item.__getitem__.return_value = 'booya.com/woot.gif'
        table.get_item.return_value = item
        image = Image('BADD00D')
        image._stored_table = table

        source_url = image.get_source_url()
        eq_(source_url, 'booya.com/woot.gif')

    def test_get_source_url__returns_none_if_no_such_image(self):
        table = Mock()
        table.get_item.side_effect = DynamoDBKeyNotFoundError('no such image')
        image = Image("TH15I5N0TEVENHEX")
        image._stored_table = table

        source_url = image.get_source_url()
        eq_(source_url, None)

