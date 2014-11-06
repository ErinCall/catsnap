from __future__ import unicode_literals

import os
import sha
import logging
import datetime
from logging.handlers import SMTPHandler
import sqlalchemy.exc
from flask import Flask, render_template, g, session, request
from flask_openid import OpenID
from catsnap.table.album import Album
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

delayed_tasks = []

@app.after_request
def after_request(response):
    session = Client().session()
    if response.status_code not in xrange(200, 399):
        session.rollback()
        return response

    try:
        session.flush()
    except sqlalchemy.exc.StatementError:
        session.rollback()
        raise

    try:
        delay_results = [task.delay(*args, **kwargs)
                         for (task, args, kwargs) in delayed_tasks]
    except StandardError:
        session.rollback()
        raise

    try:
        Client().session().commit()
    except StandardError:
        for delay_result in delay_results:
            delay_result.revoke()
        raise
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
    return render_template('index.html.jinja', albums=albums)
