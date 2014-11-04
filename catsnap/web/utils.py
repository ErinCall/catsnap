from __future__ import unicode_literals

from functools import wraps
from catsnap.web.formatted_routes import abort
from flask import g, redirect


def is_logged_in():
    return g.user is not None


def login_required(fn):
    @wraps(fn)
    def wrapper(request_format, *args, **kwargs):
        if g.user is None:
            if request_format == 'html':
                return redirect('/')
            else:
                abort(request_format, 401, "You must log in to do that.")

        else:
            return fn(request_format, *args, **kwargs)

    return wrapper
