from __future__ import unicode_literals

import os
import sha
import logging
import datetime
from logging.handlers import SMTPHandler
from flask import Flask, render_template, g, session, request
from flask_openid import OpenID
from catsnap.table.album import Album
from catsnap import Client

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
app = Flask(__name__, static_folder=os.path.join(PROJECT_ROOT, 'public'),
            static_url_path='/public')

if not app.debug and all(map(lambda x: x in os.environ,
                             ['SENDGRID_PASSWORD',
                             'SENDGRID_USERNAME',
                             'ERROR_RECIPIENT',
                             'ERROR_SENDER'])):
    mail_handler = SMTPHandler('smtp.sendgrid.net',
                               os.environ['ERROR_SENDER'],
                               [os.environ['ERROR_RECIPIENT']],
                               'Catsnap error',
                               (os.environ['SENDGRID_USERNAME'],
                                os.environ['SENDGRID_PASSWORD']))
    mail_handler.setLevel(logging.ERROR)
    mail_handler.setFormatter(logging.Formatter('''
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:

%(message)s
'''))
    app.logger.addHandler(mail_handler)

stderr_handler = logging.StreamHandler()
stderr_handler.setLevel(logging.WARNING)
app.logger.addHandler(stderr_handler)

app.secret_key = os.environ.get('CATSNAP_SECRET_KEY')
oid = OpenID(app, safe_roots=[])

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
import catsnap.web.controllers.image
import catsnap.web.controllers.album

config = Client().config()
if 'cloudfront_distribution_id' in config:
    distro_id = config['cloudfront_distribution_id']
    Client().cloudfront_url(distro_id)

@app.route('/')
def index():
    albums = Client().session().query(Album).\
        order_by(Album.name).\
        all()
    return render_template('index.html.jinja', user=g.user, albums=albums)
