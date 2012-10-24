import os
from flask import Flask, render_template, g, session
from flask_openid import OpenID

app = Flask(__name__)
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
