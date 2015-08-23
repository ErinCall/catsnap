from __future__ import unicode_literals

import os
import sha
import sys
import logging
import datetime
from logging.handlers import SMTPHandler
from flask import Flask, render_template, g, session, request
from catsnap.table.album import Album
from catsnap.db_redis_coordination import (
    coordinated_rollback,
    coordinated_commit,
)
from catsnap import Client

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
app = Flask(__name__, static_folder=os.path.join(PROJECT_ROOT, 'public'),
            static_url_path='/public')

if not app.debug and all(map(lambda x: x in os.environ,
                             ['EMAIL_HOST',
                             'ERROR_RECIPIENT',
                             'ERROR_SENDER'])):
    if 'EMAIL_USERNAME' in os.environ and 'EMAIL_PASSWORD' in os.environ:
        email_credentials = (os.environ['EMAIL_USERNAME'],
                             os.environ['EMAIL_PASSWORD'])
    else:
        email_credentials = None
    mail_handler = SMTPHandler(os.environ['EMAIL_HOST'],
                               os.environ['ERROR_SENDER'],
                               [os.environ['ERROR_RECIPIENT']],
                               'Catsnap error',
                               email_credentials)
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

@app.before_request
def before_request():
    g.queued_tasks = []
    g.user = None
    if 'logged_in' in session:
        g.user = 1

    if 'twitter_username' in Client().config():
        g.twitter_username = Client().config().twitter_username

@app.after_request
def after_request(response):
    session = Client().session()
    if response.status_code not in xrange(200, 399):
        coordinated_rollback(g.queued_tasks)
        return response

    coordinated_commit(g.queued_tasks)

    return response

import catsnap.web.controllers.login
import catsnap.web.controllers.find
import catsnap.web.controllers.image
import catsnap.web.controllers.album
import catsnap.web.controllers.websockets

config = Client().config()
if 'cloudfront_distribution_id' in config:
    distro_id = config['cloudfront_distribution_id']
    Client().cloudfront_url(distro_id)

@app.route('/')
def index():
    albums = Client().session().query(Album).\
        order_by(Album.name).\
        all()
    return render_template('index.html.jinja', albums=albums)
