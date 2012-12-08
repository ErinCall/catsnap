import os
from flask import Flask, render_template, g, session
from flask_openid import OpenID
from catsnap.web.middleware.exception_logger import ExceptionLogger
from catsnap.web.middleware.exception_notifier import ExceptionNotifier

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

import catsnap.web.controllers.login
import catsnap.web.controllers.find
import catsnap.web.controllers.add

@app.route('/')
def index():
    return render_template('index.html', user=g.user)
