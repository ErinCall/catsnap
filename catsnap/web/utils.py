from __future__ import unicode_literals

from functools import wraps
from flask import g, redirect

def is_logged_in():
    return g.user is not None

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if g.user is None:
            return redirect('/')
        else:
            return fn(*args, **kwargs)

    return wrapper

