from __future__ import unicode_literals

import sys
from functools import wraps
from flask import g
import sqlalchemy.exc
import redis.exceptions
from catsnap import Client
from catsnap.table.task_transaction import TaskTransaction

RETRY_POLICY = {
    # maximum number of retry attempts, so jobs will run up to 9 times
    # all told.
    'max_retries': 8,
    # initial delay before retrying, so the first retry will be immediate.
    'interval_start': 0,
    # Increase delay by this many seconds on subsequent retry. The 2nd retry
    # (3rd attempt) will run 0.2 seconds after the 1st, the 3rd retry will
    # run 0.4 seconds after the 2nd, etc.
    'interval_step': 0.2,
    # Once the retry delay reaches this value, stop increasing it.
    'interval_max': 1.0,
}

# Creates a transaction id and sends the task off to Celery.
# In order to accept a transaction id, the task must have been wrapped
# in wait_for_transaction.
# The first argument, queue, should be either catsnap.worker.queued_tasks
# or g.queued_tasks.
def delay(queue, task, *args, **kwargs):
    transaction_id = TaskTransaction.new_id()
    args = [str(transaction_id)] + list(args)
    task_info = task.apply_async(
        args=args,
        kwargs=kwargs,
        retry=True,
        retry_policy=RETRY_POLICY
    )
    queue.append(task_info)
    return task_info.id

def wait_for_transaction(task):
    @wraps(task)
    def wrapper(self, transaction_id, *args, **kwargs):
        session = Client().session()
        transactions_found = session.query(TaskTransaction).\
            filter(TaskTransaction.transaction_id == transaction_id).\
            delete()
        if transactions_found == 0:
            raise self.retry()
        else:
            return task(self, *args, **kwargs)

    return wrapper

# Try to commit the database. In the event of errors (especially since commit
# may imply flush), try to revoke any queued tasks. If there are *further*
# errors while trying to revoke, this'll try to raise an error that shows the
# whole situation.
def coordinated_commit(queued_tasks):
    session = Client().session()
    try:
        session.commit()
    except sqlalchemy.exc.OperationalError as sqlError:
        # If we've sent tasks to redis but have lost the database, those tasks
        # probably point to invalid data. They'll likely fail anyway when the
        # worker can't get the database, and even if they don't, whatever
        # operation they relate to has been lost.

        exc_info = sys.exc_info()
        try:
            for task in queued_tasks:
                task.revoke()
        except (redis.exceptions.ConnectionError,
                redis.exceptions.TimeoutError) as redisError:
            # If we've lost the database, redis connection errors seem likely.
            # Try to report the whole failure.
            raise SkyIsFallingError(sqlError, redisError), None, exc_info[2]

        raise sqlError, None, exc_info[2]
    except (sqlalchemy.exc.DatabaseError,
            sqlalchemy.exc.StatementError) as sqlError:
        session.rollback()
        exc_info = sys.exc_info()
        # If we've sent tasks to redis, they probably point to invalid data.
        # Even if they don't, whatever operation they relate to was invalid in
        # some way or another.
        try:
            for task in queued_tasks:
                task.revoke()
        except (redis.exceptions.ConnectionError,
                redis.exceptions.TimeoutError) as redisError:
            raise SkyIsFallingError(sqlError, redisError), None, exc_info
        raise sqlError, None, exc_info[2]

# Roll back the database and revoke all queued tasks. In the event of errors,
# try to get things in a coherent state, but still let the errors out.
def coordinated_rollback(queued_tasks):
    session = Client().session()
    try:
        session.rollback()
        for task in queued_tasks:
            task.revoke()
    except sqlalchemy.exc.OperationalError as sqlError:
        exc_info = sys.exc_info()
        try:
            # Still try to revoke all queued tasks even though the database is
            # down. If this fails too, it'll raise SkyIsFalling; if it
            # succeeds it'll reraise the sqlError.
            for task in queued_tasks:
                task.revoke()
        except (redis.exceptions.ConnectionError,
                redis.exceptions.TimeoutError) as redisError:
            raise SkyIsFallingError(sqlError, redisError), None, exc_info[2]

        raise sqlError, None, exc_info[2]


# "Y'all know it's all fucked up now, right? What the fuck I'mma do now? What
# I'mma do now? Can y'all hear me out there? Can you hear me out there! It's
# all fucked up now. What I'mma do now, huh? What I'mma do now? It's all
# fucked up now." -- P. Diddy
class SkyIsFallingError(sqlalchemy.exc.OperationalError,
                        redis.exceptions.ConnectionError):
    def __init__(self, sqlError, redisError):
        self.message = (sqlError.message +
        "\n\n###### BUT WAIT, THERE'S MORE: ######\n\n" +
        redisError.message)
