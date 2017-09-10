# This file's here to set up some env vars for the tests to enjoy accessing.

import os

if 'CATSNAP_SECRET_SESSION_KEY' not in os.environ:
    os.environ['CATSNAP_SECRET_SESSION_KEY'] = 'c2VjcmV0IHNlc3Npb24ga2V5IQ=='

# obviously this is not a redis url. Celery will take it to mean "put all
# tasks in memory." The direct redis pub/sub attachments seem to take it to
# mean "connect to the default redis config," which seems ok.
if 'CATSNAP_REDIS_URL' not in os.environ:
    os.environ['CATSNAP_REDIS_URL'] = 'memory://'
