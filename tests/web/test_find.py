import json
from mock import patch
from tests import TestCase, with_settings
from nose.tools import eq_

class TestIndex(TestCase):
    @with_settings(aws={'bucket': 'cattysnap'})
    @patch('catsnap.web.controllers.find.Tag')
    def test_find_a_tag(self, Tag):
        Tag.get_image_data.return_value = [ ('CA7', 1, 'pet cool'),
                                            ('D06', 2, 'pet')]
        response = self.app.get('/find?tags=pet')
        eq_(response.status_code, 200, response.data)
        link = '<a href="/image/%s">%s</a>'
        cat_link = link % (1, 'pet cool')
        dog_link = link % (2, 'pet')
        assert cat_link in response.data.decode('utf-8'), response.data
        assert dog_link in response.data.decode('utf-8'), response.data

    @with_settings(aws={'bucket': 'cattysnap'})
    @patch('catsnap.web.controllers.find.Tag')
    def test_search_strings_have_whitespace_trimmed(self, Tag):
        Tag.get_image_data.return_value = []
        response = self.app.get('/find?tags= pet ')

        eq_(response.status_code, 200, response.data)

        Tag.get_image_data.assert_called_with(['pet'])

    @with_settings(aws={'bucket': 'cattysnap'})
    @patch('catsnap.web.controllers.find.Tag')
    def test_find_a_tag__json_format(self, Tag):
        image_structs = [ ('CA7', 1, 'pet cool'),
                          ('D06', 2, 'pet'     )]
        Tag.get_image_data.return_value = image_structs
        response = self.app.get('/find.json?tags=pet')
        eq_(response.status_code, 200, response.data)
        eq_(json.loads(response.data.decode('utf-8')), [
            {'source_url': 'https://s3.amazonaws.com/cattysnap/CA7',
             'url': '/image/1',
             'caption': 'pet cool',},
            {'source_url': 'https://s3.amazonaws.com/cattysnap/D06',
             'url': '/image/2',
             'caption': 'pet'}])
