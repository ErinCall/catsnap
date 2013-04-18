from __future__ import unicode_literals

import base64
import os
import sha
import datetime
import time
from flask import Flask, render_template, g, session, request
from flask_openid import OpenID
from catsnap.web.middleware.exception_logger import ExceptionLogger
from catsnap.web.middleware.exception_notifier import ExceptionNotifier
from catsnap.table.album import Album
from catsnap import Client

app = Flask(__name__)

if os.environ.get('CATSNAP_ENV', None) == 'production':
    app.wsgi_app = ExceptionLogger(app.wsgi_app)
    app.wsgi_app = ExceptionNotifier(app.wsgi_app)
app.secret_key = os.environ.get('CATSNAP_SECRET_KEY')
oid = OpenID(app)

@app.before_request
def before_request():
    g.user = None
    if 'openid' in session:
        g.user = 1
    elif 'X-Catsnap-Signature' in request.headers:
        passed_signature = request.headers['X-Catsnap-Signature']
        date = request.headers['X-Catsnap-Signature-Date']
        string_to_sign = "%s\n%s" % (date, Client().config().api_key)
        generated_signature = sha.sha(string_to_sign).hexdigest()

        date = datetime.datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
        now = datetime.datetime.utcnow()
        skew = abs(date - now)
        if generated_signature == passed_signature \
                and skew.days == 0 \
                and skew.seconds <= (5*60):
            g.user = 1

@app.after_request
def after_request(response):
    Client().session().commit()
    return response

import catsnap.web.controllers.login
import catsnap.web.controllers.find
import catsnap.web.controllers.add
import catsnap.web.controllers.album

@app.route('/')
def index():
    albums = Client().session().query(Album).all()
    return render_template('index.html', user=g.user, albums=albums)
