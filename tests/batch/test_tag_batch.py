from __future__ import unicode_literals

from mock import patch, Mock
from nose.tools import eq_
from tests import TestCase

from catsnap import HASH_KEY
from catsnap.batch.tag_batch import get_tags

class TestTagBatch(TestCase):
    @patch('catsnap.batch.tag_batch.Config')
    @patch('catsnap.batch.tag_batch.BatchList')
    def test_get_tags(self, BatchList, Config):
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
                                HASH_KEY: 'cats',
                                'filenames': '["deadbeef", "badcafe", "defec8"]'},
                            {
                                HASH_KEY: 'dogs',
                                'filenames': '["5ca1ab1e", "deadbeef"]'}],
                        'ConsumedCapacityUnits': 10.0}}}
        mock_config.get_dynamodb.return_value = dynamo
        Config.return_value = mock_config
        batch_list = Mock()
        BatchList.return_value = batch_list

        tags = list(get_tags(['a', 'b']))
        BatchList.assert_called_once_with(dynamo)
        batch_list.add_batch.assert_called_once_with(
                table, ['a', 'b'], attributes_to_get=['filenames', HASH_KEY])
        dynamo.batch_get_item.assert_called_with(batch_list)
        eq_(tags, [
            {
                'tag': 'cats',
                'filenames': [ 'deadbeef', 'badcafe', 'defec8']},
            {
                'tag': 'dogs',
                'filenames': [ '5ca1ab1e', 'deadbeef']}])


    @patch('catsnap.batch.tag_batch.Config')
    @patch('catsnap.batch.tag_batch.BatchList')
    def test_get_tags__checks_back_on_unprocessed_keys(self,
            BatchList, Config):
        mock_config = Mock()
        table = Mock()
        table.name = 'thetablename'
        mock_config.table.return_value = table
        dynamo = Mock()
        first_getitem = {
                'UnprocessedKeys': {
                    'thetablename': {
                        'Keys': [ {'HashKeyElement': 'dogs'}],
                        'AttributesToGet': ['tags', HASH_KEY]}},
                'Responses': {
                    'thetablename': {
                        'Items': [
                            {
                                HASH_KEY: 'cats',
                                'filenames': '["deadbeef", "badcafe", "defec8"]'}],
                        'ConsumedCapacityUnits': 10.0}}}
        second_getitem = {
                'UnprocessedKeys': {},
                'Responses': {
                    'thetablename': {
                        'Items': [
                            {
                                HASH_KEY: 'dogs',
                                'filenames': '["5ca1ab1e", "deadbeef"]'}],
                        'ConsumedCapacityUnits': 10.0}}}
        dynamo.batch_get_item.side_effect = [first_getitem, second_getitem]
        mock_config.get_dynamodb.return_value = dynamo
        Config.return_value = mock_config
        batch_list = Mock()
        BatchList.return_value = batch_list

        tags = list(get_tags(['whatever']))
        eq_(tags, [
            {
                'tag': 'cats',
                'filenames': [ 'deadbeef', 'badcafe', 'defec8']},
            {
                'tag': 'dogs',
                'filenames': [ '5ca1ab1e', 'deadbeef']}])

    def test_get_tags__degenerate_case(self):
        eq_(list(get_tags([])), [])

