from __future__ import unicode_literals

import threading
from functools import wraps
from tests import TestCase as BaseTestCase
from werkzeug.serving import make_server
from flask import g, session, redirect
from catsnap.web import app
from splinter import Browser

web_actors = {}


class TestCase(BaseTestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.browser = web_actors['browser']


class App(object):
    def __init__(self):
        self.app = app

    def start(self):
        self.server = make_server('0.0.0.0', 65432, self.app)
        self.server.serve_forever()

    def stop(self):
        if hasattr(self, 'server'):
            self.server.shutdown()


def setUpPackage():
    test_app = App()
    thread = threading.Thread(target=test_app.start)
    thread.daemon = True
    thread.start()
    web_actors['server'] = test_app

    web_actors['browser'] = Browser()


def tearDownPackage():
    web_actors['server'].stop()
    web_actors['browser'].quit()


@app.route('/become_logged_in')
def become_logged_in():
    g.user = 1
    session['openid'] = 'booya'
    return redirect('/')


def logged_in(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        web_actors['browser'].visit('http://localhost:65432/become_logged_in')
        fn(*args, **kwargs)
    return wrapper