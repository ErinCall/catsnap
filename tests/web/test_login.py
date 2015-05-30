from __future__ import unicode_literals

import datetime
import sha
from tests import TestCase, with_settings
from nose.tools import eq_
from catsnap import Client

class TestLogin(TestCase):
    def test_requesting_login_returns_the_login_page(self):
        response = self.app.get('/login')
        eq_(response.status_code, 200)

    # password is 'supersekrit'
    @with_settings(password_hash='$2a$12$NvDhDRCb7zfKyoH5uAkdF.p'
                                 'YbD9IFXmtt2qsuT8J/mDvx13tDiD3m')
    def test_successful_login_redirects_to_home(self):
        response = self.app.post('/login', data={
            'password': 'supersekrit',
        })
        eq_(response.status_code, 302)
        eq_(response.headers['Location'], 'http://localhost/')

    # password is 'supersekrit'
    @with_settings(password_hash='$2a$12$NvDhDRCb7zfKyoH5uAkdF.p'
                                 'YbD9IFXmtt2qsuT8J/mDvx13tDiD3m')
    def test_successful_login_redirects_to_next_param(self):
        response = self.app.post('/login', data={
            'password': 'supersekrit',
            'next': '/image/1234',
        })
        eq_(response.status_code, 302, response.data)
        eq_(response.headers['Location'], 'http://localhost/image/1234')
