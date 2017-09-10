import json
from tests import TestCase
from catsnap import Client
from catsnap.table.image import Image
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

    @formatted_route('/test/lazy/json/route')
    def json_action_that_returns_an_object(request_format):
        if request_format == 'json':
            return {'current status': 'lazy'}
        else:
            raise NotImplementedError

    @formatted_route('/test/fancy/formatted/route', methods=['GET'] )
    def fancy_action_default_lizard(request_format):
        return json.dumps({'request_format': request_format,
                           'lizard': 'charmander'})

    @formatted_route('/test/fancy/formatted/route/<lizard>')
    def fancy_action_explicit_lizard(request_format, lizard):
        return json.dumps({'request_format': request_format, 'lizard': lizard})

    @formatted_route('/test/bad/image/id', methods=['GET'])
    def bad_image_id_action(self):
        Client().session().query(Image).filter(Image.image_id == 1).one()

    def test_defaults_to_html_format(self):
        response = self.app.get('/test/formatted/route')
        eq_(response.data, b'HTML')

    def test_html_format(self):
        response = self.app.get('/test/formatted/route.html',
                                follow_redirects=True)
        eq_(response.data, b'HTML')

    def test_json_format(self):
        response = self.app.get('/test/formatted/route.json')
        eq_(response.data, b'JSON')
        eq_(response.headers['Content-Type'],
                'application/json')

    def test_invalid_format(self):
        response = self.app.get('/test/formatted/route.chubbybunnies')
        eq_(response.status_code, 400)
        eq_(response.data, b"Unknown format 'chubbybunnies'")

    def test_set_format_on_request_header(self):
        response = self.app.get('/test/formatted/route',
                                headers={'Accept':'application/json'})
        eq_(response.data, b'JSON')

    def test_get_fancy_action__routed_default(self):
        response = self.app.get('/test/fancy/formatted/route')
        body = json.loads(response.data.decode('utf-8'))
        eq_(body, {'request_format': 'html', 'lizard': 'charmander'})

    def test_get_fancy_action__with_params(self):
        response = self.app.get('/test/fancy/formatted/route/komodo.json')
        body = json.loads(response.data.decode('utf-8'))
        eq_(body, {'request_format': 'json', 'lizard': 'komodo'})

    def test_json_actions_can_return_objects(self):
        response = self.app.get('/test/lazy/json/route.json')
        eq_(response.data, b'{"current status": "lazy"}')

    def test_returns_404_on_no_result_found(self):
        response = self.app.get('/test/bad/image/id.json')
        eq_(response.status_code, 404)
