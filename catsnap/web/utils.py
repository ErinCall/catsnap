from __future__ import unicode_literals

from functools import wraps
from flask import g, redirect, abort


def is_logged_in():
    return g.user is not None


def login_required(fn):
    @wraps(fn)
    def wrapper(request_format, *args, **kwargs):
        if g.user is None:
            if request_format == 'html':
                return redirect('/')
            else:
                abort(401)

        else:
            return fn(request_format, *args, **kwargs)

    return wrapper
