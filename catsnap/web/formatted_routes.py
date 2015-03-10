from __future__ import unicode_literals

import json
from functools import wraps
from flask import request, make_response, abort as flask_abort
from catsnap.web import app

def formatted_route(route, defaults={}, **kwargs):
    def decorator(fn):
        @app.route(route,
                   defaults=dict(request_format='html', **defaults),
                   **kwargs)
        @app.route('%s.<request_format>' % route, defaults=defaults, **kwargs)
        @wraps(fn)
        def wrapper(request_format, *args, **kwargs):
            if 'Accept' in request.headers \
                    and request.headers['Accept'] == 'application/json':
                request_format = 'json'
            if request_format not in ['json', 'html']:
                abort(request_format,
                      400,
                      "Unknown format '{0}'".format(request_format))

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

def abort(request_format, code, message=None):
    if request_format == 'json':
        flask_abort(make_response(json.dumps({'error': message, 'status': 'error'}),
                                  code,
                                  {'Content-Type': 'application/json'}))
    else:
        flask_abort(make_response(message, code))
