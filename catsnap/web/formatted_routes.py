from __future__ import unicode_literals

from functools import wraps
from flask import make_response
from catsnap.web import app

def formatted_route(route, defaults={}, **kwargs):
    def decorator(fn):
        defaults.update({'request_format':'html'})
        @app.route(route, defaults=defaults, **kwargs)
        @app.route('%s.<request_format>' % route, **kwargs)
        @wraps(fn)
        def wrapper(request_format, *args, **kwargs):
            if request_format not in ['json', 'html']:
                return make_response("Unknown format '%s'" % request_format,
                                     400)
            return fn(request_format, *args, **kwargs)
        return wrapper
    return decorator
