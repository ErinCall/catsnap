import os
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
config = Client().config()

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
app = Flask(__name__, static_folder=os.path.join(PROJECT_ROOT, 'public'),
            static_url_path='/public')

if not app.debug and all([x in config for x in ['error_email.provider.hostname',
                             'error_email.recipient',
                             'error_email.sender']]):
    if ('error_email.provider.username' in config
            and 'error_email.provider.password' in config):
        email_credentials = (config['error_email.provider.username'],
                             config['error_email.provider.password'])
    else:
        email_credentials = None
    mail_handler = SMTPHandler(config['error_email.provider.hostname'],
                               config['error_email.sender'],
                               [config['error_email.recipient']],
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

app.secret_key = config['secret_session_key']

@app.before_request
def before_request():
    g.queued_tasks = []
    g.user = None
    if 'logged_in' in session:
        g.user = 1

    if 'twitter_username' in config:
        g.twitter_username = config['twitter_username']

@app.after_request
def after_request(response):
    session = Client().session()
    if response.status_code not in range(200, 399):
        coordinated_rollback(g.queued_tasks)
        return response

    coordinated_commit(g.queued_tasks)

    return response

import catsnap.web.controllers.login
import catsnap.web.controllers.find
import catsnap.web.controllers.image
import catsnap.web.controllers.album
import catsnap.web.controllers.websockets

if 'aws.cloudfront_distribution_id' in config:
    distro_id = config['aws.cloudfront_distribution_id']
    Client().cloudfront_url(distro_id)

@app.route('/')
def index():
    albums = Client().session().query(Album).\
        order_by(Album.name).\
        all()
    return render_template('index.html.jinja', albums=albums)
