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

@task_success.connect
def after_task(**kwargs):
    Client().session().commit()

import catsnap.worker.tasks
