from __future__ import unicode_literals

from mock import patch, Mock, MagicMock
from nose.tools import eq_
from tests import TestCase

from catsnap.document import Document

class TestBaseBehavior(TestCase):
    @patch('catsnap.document.Client')
    def test_get_table_creates_table_conection(self, Client):
        client = Mock()
        Client.return_value = client
        mock_table = Mock()
        client.table.return_value = mock_table

        document = Document()
        document._table_name = 'grouchy'
        table = document._table()
        eq_(document._stored_table, mock_table)
        eq_(table, mock_table)
        client.table.assert_called_with('grouchy')

    @patch('catsnap.document.Client')
    def test_get_table_is_memoized(self, Client):
        client = Mock()
        Client.return_value = client
        document = Document()
        mock_table = Mock()
        document._stored_table = mock_table

        table = document._table()
        eq_(table, mock_table)
        eq_(client.table.call_count, 0)
