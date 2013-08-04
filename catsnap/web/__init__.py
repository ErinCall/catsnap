from __future__ import unicode_literals

import os
import sha
import logging
import datetime
from logging.handlers import SMTPHandler
from flask import Flask, render_template, g, session, request
from flask_openid import OpenID
from flask.ext.assets import Environment, Bundle
from catsnap.table.album import Album
from catsnap import Client

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
app = Flask(__name__,
            static_folder=os.path.join(PROJECT_ROOT, 'public'),
            static_url_path='/public')

if 'SENDGRID_PASSWORD' in os.environ and not app.debug:
    mail_handler = SMTPHandler('smtp.sendgrid.net',
                               'errors@radlibs.info',
                               ['andrew.lorente@gmail.com'],
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

app.secret_key = os.environ.get('CATSNAP_SECRET_KEY')
oid = OpenID(app)


if os.getenv('ASSETS_DEBUG'):
    app.config['ASSETS_DEBUG'] = True
assets = Environment(app)
js = Bundle('js/jquery-2.0.0.min.js',
            'js/bootstrap.min.js',
            'js/underscore-min.js',
            'js/edit_image.js',
            filters='jsmin',
            output='gen/packed.js')
assets.register('js_all', js)
css = Bundle("css/bootstrap.min.css",
             "css/layout.css",
             filters='cssmin',
             output='gen/packed.css')
assets.register('css_all', css)


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


@app.route('/')
def index():
    albums = Client().session().query(Album).all()
    return render_template('index.html.jinja', user=g.user, albums=albums)
