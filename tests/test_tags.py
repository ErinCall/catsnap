from __future__ import unicode_literals

from mock import patch, Mock, call
from nose.tools import eq_, raises

from catsnap.tag import Tag

class TestTags():
    def test_save__sends_to_dynamo(self):
        table = Mock()
        item = Mock()
        tag = Tag('cat')
        table.new_item.return_value = item

        tag.save(table,  'Sewing_cat.gif')
        table.new_item.assert_called_with(hash_key='cat',
                attrs={ 'Sewing_cat.gif': 'Sewing_cat.gif'})
        item.put.assert_called_with()
