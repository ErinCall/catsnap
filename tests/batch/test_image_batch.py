from __future__ import unicode_literals

from mock import patch, Mock
from nose.tools import eq_
from tests import TestCase

from catsnap import HASH_KEY
from catsnap.batch.image_batch import get_images

class TestImageBatch(TestCase):
    @patch('catsnap.batch.image_batch.Config')
    @patch('catsnap.batch.image_batch.BatchList')
    def test_get_images(self, BatchList, Config):
        mock_config = Mock()
        table = Mock()
        table.name = 'the-name-of-the-table'
        mock_config.table.return_value = table
        dynamo = Mock()
        dynamo.batch_get_item.return_value = {
                'UnprocessedKeys': {},
                'Responses': {
                    'the-name-of-the-table': {
                        'Items': [
                            {
                                HASH_KEY: 'deadbeef',
                                'tags': '["cream", "cat", "money"]'},
                            {
                                HASH_KEY: 'badcafe',
                                'tags': '["evil", "nefarious", "cat"]'}],
                        'ConsumedCapacityUnits': 10.0}}}
        mock_config.get_dynamodb.return_value = dynamo
        Config.return_value = mock_config
        batch_list = Mock()
        BatchList.return_value = batch_list

        images = list(get_images(['a', 'b']))
        BatchList.assert_called_once_with(dynamo)
        batch_list.add_batch.assert_called_once_with(
                table, ['a', 'b'], attributes_to_get=['tags', HASH_KEY])
        dynamo.batch_get_item.assert_called_with(batch_list)
        eq_(images, self._standard_fixture_images())


    @patch('catsnap.batch.image_batch.Config')
    @patch('catsnap.batch.image_batch.BatchList')
    def test_get_images__checks_back_on_unprocessed_keys(self,
            BatchList, Config):
        mock_config = Mock()
        table = Mock()
        table.name = 'thetablename'
        mock_config.table.return_value = table
        dynamo = Mock()
        first_getitem = {
                'UnprocessedKeys': {
                    'thetablename': {
                        'Keys': [
                            {'HashKeyElement':
                                'badcafe'}],
                        'AttributesToGet': ['tags', HASH_KEY]}},
                'Responses': {
                    'thetablename': {
                        'Items': [
                            {
                                HASH_KEY: 'deadbeef',
                                'tags': '["cream", "cat", "money"]'}],
                        'ConsumedCapacityUnits': 10.0}}}
        second_getitem = {
                'UnprocessedKeys': {},
                'Responses': {
                    'thetablename': {
                        'Items': [
                            {
                                HASH_KEY: 'badcafe',
                                'tags': '["evil", "nefarious", "cat"]'}],
                        'ConsumedCapacityUnits': 10.0}}}
        dynamo.batch_get_item.side_effect = [first_getitem, second_getitem]
        mock_config.get_dynamodb.return_value = dynamo
        Config.return_value = mock_config
        batch_list = Mock()
        BatchList.return_value = batch_list

        images = list(get_images(['whatever']))
        eq_(images, self._standard_fixture_images())

    def _standard_fixture_images(self):
        return [
            {
                'filename': 'deadbeef',
                'tags': [ 'cream', 'cat', 'money' ]},
            {
                'filename': 'badcafe',
                'tags': ['evil', 'nefarious', 'cat']}]
