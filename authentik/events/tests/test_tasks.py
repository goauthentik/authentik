"""Test Monitored tasks"""
from django.test import TestCase

from authentik.events.monitored_tasks import MonitoredTask, TaskInfo, TaskResult, TaskResultStatus
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
            self.set_status(
                TaskResult(TaskResultStatus.ERROR if should_fail else TaskResultStatus.SUCCESSFUL)
            )

        # First test successful run
        should_fail = False
        test_task.delay().get()
        self.assertIsNone(TaskInfo.by_name(f"test_task:{uid}"))

        # Then test failed
        should_fail = True
        test_task.delay().get()
        info = TaskInfo.by_name(f"test_task:{uid}")
        self.assertEqual(info.result.status, TaskResultStatus.ERROR)

        # Then after that, the state should be removed
        should_fail = False
        test_task.delay().get()
        self.assertIsNone(TaskInfo.by_name(f"test_task:{uid}"))
