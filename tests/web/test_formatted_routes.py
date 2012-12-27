from __future__ import unicode_literals

import json
from tests import TestCase
from catsnap.web.formatted_routes import formatted_route
from nose.tools import eq_

class TestFormattedRoute(TestCase):
    @formatted_route('/test/formatted/route')
    def action(request_format):
        if request_format == 'json':
            return "JSON"
        elif request_format == 'html':
            return "HTML"
        else:
            raise AssertionError("Received an unknown format: '%s'" %
                                 request_format)

    def test_defaults_to_html_format(self):
        response = self.app.get('/test/formatted/route')
        eq_(response.data, 'HTML')

    def test_html_format(self):
        response = self.app.get('/test/formatted/route.html',
                                follow_redirects=True)
        eq_(response.data, 'HTML')

    def test_json_format(self):
        response = self.app.get('/test/formatted/route.json')
        eq_(response.data, 'JSON')
        eq_(response.headers['Content-Type'],
                'application/json')

    def test_invalid_format(self):
        response = self.app.get('/test/formatted/route.chubbybunnies')
        eq_(response.status_code, 400)
        eq_(response.data, "Unknown format 'chubbybunnies'")

    def test_set_format_on_request_header(self):
        response = self.app.get('/test/formatted/route',
                                headers={'Accept':'application/json'})
        eq_(response.data, 'JSON')

    @formatted_route('/test/fancy/formatted/route',
                     methods=['GET'],
                     defaults={'lizard': 'charmander'})
    @formatted_route('/test/fancy/formatted/route/<lizard>')
    def fancy_action(request_format, lizard):
        return json.dumps({'request_format': request_format, 'lizard': lizard})

    def test_get_fancy_action__routed_default(self):
        response = self.app.get('/test/fancy/formatted/route')
        body = json.loads(response.data)
        eq_(body, {'request_format': 'html', 'lizard': 'charmander'})

    def test_get_fancy_action__with_params(self):
        response = self.app.get('/test/fancy/formatted/route/komodo.json')
        body = json.loads(response.data)
        eq_(body, {'request_format': 'json', 'lizard': 'komodo'})

    @formatted_route('/test/lazy/json/route')
    def json_action_that_returns_an_object(request_format):
        if request_format == 'json':
            return {'current status': 'lazy'}
        else:
            raise NotImplementedError

    def test_json_actions_can_return_objects(self):
        response = self.app.get('/test/lazy/json/route.json')
        eq_(response.data, '{"current status": "lazy"}')
