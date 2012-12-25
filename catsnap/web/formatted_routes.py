from __future__ import unicode_literals

import json
from functools import wraps
from flask import request, make_response
from catsnap.web import app

def formatted_route(route, defaults={}, **kwargs):
    def decorator(fn):
        defaults.update({'request_format':'html'})
        @app.route(route, defaults=defaults, **kwargs)
        @app.route('%s.<request_format>' % route, **kwargs)
        @wraps(fn)
        def wrapper(request_format, *args, **kwargs):
            if 'Accept' in request.headers \
                    and request.headers['Accept'] == 'application/json':
                request_format = 'json'
            if request_format not in ['json', 'html']:
                return make_response("Unknown format '%s'" % request_format,
                                     400)

            response = fn(request_format, *args, **kwargs)
            if request_format == 'json':
                if type(response) in [list, dict]:
                    response = json.dumps(response)

                if type(response) in [unicode, str]:
                    response = make_response(response)

                response.headers['Content-Type'] = 'application/json'
            return response
        return wrapper
    return decorator
