from __future__ import unicode_literals

from celery import Celery
from celery.signals import task_success
import os

if os.environ.get('ENV') and os.path.exists(os.environ['ENV']):
    for line in open(os.environ['ENV']):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]

from catsnap import Client

broker_url = Client().config().celery_broker_url

worker = Celery('catsnap.worker', broker=broker_url)
worker.conf.CELERY_TASK_SERIALIZER = 'json'
if all(map(lambda x: x in os.environ,
           ['EMAIL_HOST', 'ERROR_RECIPIENT', 'ERROR_SENDER'])):
    worker.conf.CELERY_SEND_TASK_ERROR_EMAILS = True
    worker.conf.ADMINS = [(os.environ['ERROR_RECIPIENT'],
                           os.environ['ERROR_RECIPIENT'])]
    worker.conf.SERVER_EMAIL = os.environ['ERROR_SENDER']
    worker.conf.EMAIL_HOST = os.environ['EMAIL_HOST']
    if 'EMAIL_USERNAME' in os.environ and 'EMAIL_PASSWORD' in os.environ:
        worker.conf.EMAIL_HOST_USER = os.environ['EMAIL_USERNAME']
        worker.conf.EMAIL_HOST_PASSWORD = os.environ['EMAIL_PASSWORD']

@task_success.connect
def after_task(**kwargs):
    Client().session().commit()

import catsnap.worker.tasks
