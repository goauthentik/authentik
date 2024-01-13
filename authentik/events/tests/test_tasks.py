"""Test Monitored tasks"""
from django.test import TestCase

from authentik.events.models import SystemTask, TaskStatus
from authentik.events.monitored_tasks import MonitoredTask
from authentik.lib.generators import generate_id
from authentik.root.celery import CELERY_APP


class TestMonitoredTasks(TestCase):
    """Test Monitored tasks"""

    def test_failed_successful_remove_state(self):
        """Test that a task with `save_on_success` set to `False` that failed saves
        a state, and upon successful completion will delete the state"""
        should_fail = True
        uid = generate_id()

        @CELERY_APP.task(
            bind=True,
            base=MonitoredTask,
        )
        def test_task(self: MonitoredTask):
            self.save_on_success = False
            self.set_uid(uid)
            self.set_status(TaskStatus.ERROR if should_fail else TaskStatus.SUCCESSFUL)

        # First test successful run
        should_fail = False
        test_task.delay().get()
        self.assertIsNone(SystemTask.objects.filter(name="test_task", uid=uid))

        # Then test failed
        should_fail = True
        test_task.delay().get()
        info = SystemTask.objects.filter(name="test_task", uid=uid)
        self.assertEqual(info.status, TaskStatus.ERROR)

        # Then after that, the state should be removed
        should_fail = False
        test_task.delay().get()
        self.assertIsNone(SystemTask.objects.filter(name="test_task", uid=uid))
