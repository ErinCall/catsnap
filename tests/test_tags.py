from __future__ import unicode_literals

from mock import patch, Mock, call, MagicMock
from nose.tools import eq_, raises
from boto.dynamodb.exceptions import DynamoDBKeyNotFoundError

from catsnap.tag import Tag

class TestTags():
    def test_save__sends_to_dynamo(self):
        table = Mock()
        item = Mock()
        tag = Tag('cat')
        table.get_item.side_effect = DynamoDBKeyNotFoundError('no such tag')
        table.new_item.return_value = item

        tag.save(table, 'Sewing_cat.gif')
        table.new_item.assert_called_with(hash_key='cat',
                attrs={ 'Sewing_cat.gif': 'Sewing_cat.gif'})
        item.put.assert_called_with()

    def test_save__updates_existing_tag(self):
        table = Mock()
        item = MagicMock()
        table.get_item.return_value = item

        tag = Tag('cat')
        tag.save(table, 'Other_cat.gif')

        eq_(table.new_item.call_count, 0, "shouldn't've made a new entry")
        item.put.assert_called_with()
        item.__setitem__.assert_called_with('Other_cat.gif', 'Other_cat.gif')

    def test_get_images(self):
        tag = Tag('cat')
        item = MagicMock()
        item.keys.return_value = ['tag', 'BADCAFE', 'DEADBEEF']
        table = Mock()
        table.get_item.return_value = item

        images = tag.get_images(table)
        eq_(images, ['BADCAFE', 'DEADBEEF'])
        table.get_item.assert_called_with('cat')

    def test_get_images__returns_empty_list_if_tag_is_not_found(self):
        tag = Tag('cat')
        table = Mock()
        table.get_item.side_effect = DynamoDBKeyNotFoundError('no such tag')

        eq_(tag.get_images(table), [])