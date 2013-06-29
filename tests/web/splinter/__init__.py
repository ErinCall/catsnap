from __future__ import unicode_literals

import os
import subprocess
from functools import wraps
from tests import TestCase as BaseTestCase, db_info
from splinter import Browser

package_vars = {}


class TestCase(BaseTestCase):
    def setUp(self):
        super(TestCase, self).setUp()
        self.browser = package_vars['browser']

    def visit(self, path):
        self.browser.visit('http://localhost:65432/%s' % path)


def setUpPackage():
    server_script = os.path.join(os.path.dirname(__file__),
                                 '..', '..', '..', 'catsnap', 'app.py')
    env = {
        'CATSNAP_BUCKET': 'cattysnap',
        'CATSNAP_SECRET_KEY': 'asdf',
        'DATABASE_URL': db_info['temp_db_url'],
        'CATSNAP_BACKDOOR': '1',
        'CATSNAP_DEBUG': '1',
        'PORT': '65432',
    }
    env.update(os.environ)
    package_vars['server'] = subprocess.Popen(['python', server_script],
                                              env=env)
    package_vars['browser'] = Browser()


def tearDownPackage():
    import signal
    try:
        package_vars['server'].send_signal(signal.SIGINT)
    finally:
        package_vars['browser'].quit()


def logged_in(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        package_vars['browser'].visit(
            'http://localhost:65432/become_logged_in')
        fn(*args, **kwargs)
    return wrapper
