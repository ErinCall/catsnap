from __future__ import unicode_literals

from mock import patch, Mock, MagicMock
from nose.tools import eq_
from boto.dynamodb.exceptions import DynamoDBKeyNotFoundError
from tests import TestCase

from catsnap.document.tag import Tag
from catsnap import HASH_KEY

class TestAddingFile(TestCase):
    def test_sends_to_dynamo(self):
        item = MagicMock()
        table = Mock()
        table.get_item.side_effect = DynamoDBKeyNotFoundError('no such tag')
        table.new_item.return_value = item
        tag = Tag('cat')
        tag._stored_table = table

        tag.add_file('Sewing_cat.gif')
        table.new_item.assert_called_with(hash_key='cat', attrs ={})
        item.__setitem__.assert_called_with('filenames', '["Sewing_cat.gif"]')
        item.put.assert_called_with()

    def test_updates_existing_tag(self):
        table = Mock()
        item = MagicMock()
        item.__getitem__.return_value = '[ "Sewing_cat.gif" ]'
        table.get_item.return_value = item

        tag = Tag('cat')
        tag._stored_table = table
        tag.add_file('other_cat.gif')

        eq_(table.new_item.call_count, 0, "shouldn't've made a new entry")
        item.__setitem__.assert_called_with('filenames',
                '["Sewing_cat.gif", "other_cat.gif"]')
        item.put.assert_called_with()

    def test_appended_filenames_are_unique(self):
        table = Mock()
        item = MagicMock()
        item.__getitem__.return_value = '[ "Sewing_cat.gif" ]'
        table.get_item.return_value = item

        tag = Tag('cat')
        tag._stored_table = table
        tag.add_file('Sewing_cat.gif')
        item.__setitem__.assert_called_with('filenames', '["Sewing_cat.gif"]')

class TestGetFilenames(TestCase):
    def test_get_filenames(self):
        item = MagicMock()
        item.__getitem__.return_value = '["BADCAFE", "DEADBEEF"]'
        table = Mock()
        table.get_item.return_value = item
        tag = Tag('cat')
        tag._stored_table = table

        filenames = tag.get_filenames()
        eq_(filenames, ['BADCAFE', 'DEADBEEF'])
        table.get_item.assert_called_with('cat')

    def test_returns_empty_list_if_no_such_tag_exists(self):
        tag = Tag('cat')
        table = Mock()
        table.get_item.side_effect = DynamoDBKeyNotFoundError('no such tag')
        tag._stored_table = table

        eq_(tag.get_filenames(), [])
