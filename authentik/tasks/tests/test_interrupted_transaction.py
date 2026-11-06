from collections.abc import Callable

from django.conf import settings
from django.db import connection, transaction
from django.test import TransactionTestCase, override_settings
from django_dramatiq_postgres.broker import PostgresBroker, discard_interrupted_transactions
from django_dramatiq_postgres.middleware import DbConnectionMiddleware
from django_dramatiq_postgres.models import TaskState
from dramatiq.broker import MessageProxy
from dramatiq.message import Message
from dramatiq.middleware import Middleware
from dramatiq.middleware.time_limit import TimeLimitExceeded

from authentik.tasks.models import Task
from authentik.tenants.utils import get_current_tenant

# What a TimeLimitExceeded raised while Django enters or leaves an atomic block leaves behind
LEFTOVERS: dict[str, Callable[[], None]] = {
    "atomic block never left": lambda: transaction.atomic().__enter__(),
    "autocommit never turned back on": lambda: connection.set_autocommit(False),
}


@override_settings(DRAMATIQ={**settings.DRAMATIQ, "test": False})
class TestInterruptedTransaction(TransactionTestCase):
    """A time limit can interrupt a task while Django enters or leaves an atomic block"""

    def setUp(self):
        self.addCleanup(discard_interrupted_transactions)
        self.broker = PostgresBroker()
        self.broker.add_middleware(DbConnectionMiddleware())
        self.message = MessageProxy(
            Message(queue_name="default", actor_name="test.actor", args=(), kwargs={}, options={})
        )

    def test_after_process_message_hooks_run_outside_the_transaction(self):
        """after_process_message hooks run on the task's tenant, outside the transaction"""
        seen = []

        class Probe(Middleware):
            def after_process_message(self, broker, message, *, result=None, exception=None):
                seen.append(
                    (connection.in_atomic_block, connection.get_autocommit(), connection.tenant)
                )

        self.broker.add_middleware(Probe())
        tenant = get_current_tenant()
        for name, leave_transaction in LEFTOVERS.items():
            with self.subTest(name):
                seen.clear()
                # TenantMiddleware.before_process_message
                tenant.activate()
                leave_transaction()

                self.broker.emit_after(
                    "process_message", self.message, exception=TimeLimitExceeded()
                )

                self.assertEqual(seen, [(False, True, tenant)])

    def test_ack_after_dropped_connection(self):
        """The ack doesn't fail forever once DbConnectionMiddleware closed the connection"""
        consumer = self.broker.consume(queue_name="default")
        Task.objects.create(
            message_id=self.message.message_id,
            queue_name="default",
            actor_name="test.actor",
            message=self.message.encode(),
            state=TaskState.RUNNING,
            tenant=get_current_tenant(),
        )
        # A hook can still leave a transaction behind after emit_after cleaned up
        transaction.atomic().__enter__()
        # DbConnectionMiddleware.after_process_message, which runs right before the ack
        DbConnectionMiddleware().after_process_message(self.broker, self.message)

        consumer.ack(self.message)

        self.assertEqual(Task.objects.get(message_id=self.message.message_id).state, TaskState.DONE)
