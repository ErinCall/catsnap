from __future__ import unicode_literals

import uuid
from contextlib import contextmanager
from mock import patch, Mock
from nose.tools import eq_, assert_raises, nottest
from sqlalchemy.exc import IntegrityError, OperationalError
from redis.exceptions import TimeoutError
from celery.exceptions import Retry
from tests import TestCase
from catsnap.worker import worker

from catsnap import Client
from catsnap.db_redis_coordination import (
    RETRY_POLICY,
    delay,
    wait_for_transaction,
    coordinated_commit,
    coordinated_rollback,
    SkyIsFallingError,
    )
from catsnap.table.task_transaction import TaskTransaction
from catsnap.table.image_tag import ImageTag

class TestDelay(TestCase):
    def test_creates_transaction_id_and_schedules_task(self):
        task = Mock()
        task_info = Mock()
        task_info.id = 'I AM A TASK ID'
        task.apply_async.return_value = task_info
        queue = []
        task_id = delay(queue, task, 'hello', one=1)

        session = Client().session()
        transaction = session.query(TaskTransaction).one()
        task.apply_async.assert_called_once_with(
            kwargs={'one': 1},
            args=[str(transaction.transaction_id), 'hello'],
            retry=True,
            retry_policy=RETRY_POLICY,
        )

        eq_(task_id, 'I AM A TASK ID')
        eq_(queue, [task_info])


class TestWaitForTransaction(TestCase):
    def test_runs_if_transaction_found(self):
        raw_task = self.mock_task()
        task = worker.task(wait_for_transaction(raw_task), bind=True)
        transaction_id = TaskTransaction.new_id()
        task(transaction_id)

        raw_task.assert_called_once_with(task)

    def test_retries_if_no_transaction_found(self):
        raw_task = self.mock_task()
        raw_task.side_effect = AssertionError("Shouldn't be called!")
        task = worker.task(wait_for_transaction(raw_task), bind=True)
        transaction_id = uuid.uuid4()

        assert_raises(Retry, lambda: task(transaction_id))


    def test_transaction_is_deleted_after_running(self):
        raw_task = self.mock_task()
        task = worker.task(wait_for_transaction(raw_task), bind=True)
        transaction_id = TaskTransaction.new_id()
        task(transaction_id)

        transactions = Client().session().query(TaskTransaction).all()
        eq_(transactions, [])

    def test_only_deletes_appropriate_transaction(self):
        raw_task = self.mock_task()
        task = worker.task(wait_for_transaction(raw_task), bind=True)
        transaction_id = TaskTransaction.new_id()
        other_transaction_id = TaskTransaction.new_id()
        task(transaction_id)

        session = Client().session()
        transaction_ids = session.query(TaskTransaction.transaction_id).all()
        eq_(transaction_ids, [(other_transaction_id,)])

    @nottest
    def mock_task(self):
        raw_task = Mock()
        # functools.wraps requires the wrapped thing to have a __name__ attr,
        # which Mock()s don't usually have. However, Celery seems to be doing
        # some fancy behind-the-scenes caching on tasks' __name__, such that
        # tests pollute each other if the names aren't unique.
        raw_task.__name__ = str(uuid.uuid4())
        return raw_task

class TestCoordinatedCommit(TestCase):
    def test_commits_in_the_happy_case(self):
        session = Client().session()
        task = Mock()
        with session_cleanup():
            session.commit = Mock()
            session.rollback = Mock()
            session.rollback.side_effect = \
                    AssertionError("Shouldn't've been called")

            coordinated_commit([task])

            session.commit.assert_called_once_with()

    def test_revokes_tasks_and_rolls_back_on_data_error(self):
        session = Client().session()
        # invalid foreign keys ahoy!
        session.add(ImageTag(image_id=8675309, tag_id=8675309))
        task = Mock()
        with session_cleanup():
            session.rollback = Mock()

            assert_raises(IntegrityError, lambda: coordinated_commit([task]))

            session.rollback.assert_called_once_with()
            task.revoke.assert_called_once_with()

    def test_revokes_tasks_on_connection_error(self):
        session = Client().session()
        task = Mock()
        with session_cleanup():
            session.rollback = Mock()
            session.rollback.side_effect = AssertionError(
                    "Don't try to roll back when the db is unavailable")
            session.commit = Mock()
            session.commit.side_effect = \
                    OperationalError(None, None, 'database timeout')

            assert_raises(OperationalError, lambda: coordinated_commit([task]))

            task.revoke.assert_called_once_with()

    def test_sky_is_falling_if_database_and_redis_are_unreachable(self):
        session = Client().session()
        task = Mock()
        task.revoke.side_effect = TimeoutError('go sit in the corner')
        with session_cleanup():
            session.rollback = Mock()
            session.rollback.side_effect = AssertionError(
                    "Don't try to roll back when the db is unavailable")
            session.commit = Mock()
            session.commit.side_effect = \
                    OperationalError(None, None, b'database timeout')

            assert_raises(SkyIsFallingError,
                          lambda: coordinated_commit([task]))

            task.revoke.assert_called_once_with()

class TestCoordinatedRollback(TestCase):
    def test_revokes_tasks_and_rolls_back_in_the_happy_case(self):
        session = Client().session()
        task = Mock()
        with session_cleanup():
            session.rollback = Mock()

            coordinated_rollback([task])

            session.rollback.assert_called_once_with()
            task.revoke.assert_called_once_with()

    def test_revokes_tasks_on_connection_error(self):
        session = Client().session()
        task = Mock()
        with session_cleanup():
            session.rollback = Mock()
            session.rollback.side_effect = \
                    OperationalError(None, None, 'database timeout')

            assert_raises(OperationalError,
                          lambda: coordinated_rollback([task]))

            task.revoke.assert_called_once_with()

    def test_sky_is_falling_if_database_and_redis_are_unreachable(self):
        session = Client().session()
        task = Mock()
        task.revoke.side_effect = TimeoutError('go sit in the corner')
        with session_cleanup():
            session.rollback = Mock()
            session.rollback.side_effect = \
                    OperationalError(None, None, b'database timeout')

            assert_raises(SkyIsFallingError,
                          lambda: coordinated_rollback([task]))

            task.revoke.assert_called_once_with()


@contextmanager
def session_cleanup():
    session = Client().session()
    commit = session.commit
    rollback = session.rollback
    flush = session.flush
    try:
        yield
    finally:
        session.commit = commit
        session.rollback = rollback
        session.flush = flush
