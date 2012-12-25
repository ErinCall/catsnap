from __future__ import unicode_literals

from mock import patch
from tests import TestCase, with_settings
from nose.tools import eq_

class TestIndex(TestCase):
    @with_settings(bucket='cattysnap')
    @patch('catsnap.web.controllers.find.Tag')
    def test_find_a_tag(self, Tag):
        Tag.get_image_data.return_value = [ ('CA7', ['pet', 'cool']),
                                            ('D06', ['pet']        )]
        response = self.app.get('/find?find_tags=pet')
        eq_(response.status_code, 200, response.data)
        link = '<a href="https://s3.amazonaws.com/cattysnap/%s">%s</a>'
        cat_link = link % ('CA7', 'pet cool')
        dog_link = link % ('D06', 'pet')
        assert cat_link in response.data, response.data
        assert dog_link in response.data, response.data
