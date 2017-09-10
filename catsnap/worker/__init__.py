from celery import Celery
from celery.signals import task_success
from catsnap.db_redis_coordination import coordinated_commit
from catsnap import Client
config = Client().config()

broker_url = config['redis_url']

worker = Celery('catsnap.worker', broker=broker_url)
worker.conf.CELERY_TASK_SERIALIZER = 'json'
worker.conf.CELERY_ACCEPT_CONTENT = ['json']

if all([x in config for x in ['error_email.provider.hostname',
           'error_email.recipient',
           'error_email.sender']]):
    worker.conf.CELERY_SEND_TASK_ERROR_EMAILS = True
    worker.conf.ADMINS = [(config['error_email.recipient'],
                           config['error_email.recipient'])]
    worker.conf.SERVER_EMAIL = config['error_email.sender']
    worker.conf.EMAIL_HOST = config['error_email.provider.hostname']
    if ('error_email.provider.username' in config
            and 'error_email.provider.password' in config):
        worker.conf.EMAIL_HOST_USER = config['error_email.provider.username']
        worker.conf.EMAIL_HOST_PASSWORD = config['error_email.provider.password']

queued_tasks = []

@task_success.connect
def after_task(**kwargs):
    coordinated_commit(queued_tasks)

import catsnap.worker.tasks
