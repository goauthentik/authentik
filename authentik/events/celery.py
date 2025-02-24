from time import sleep

from celery.events import EventReceiver
from celery.events.state import State
from prometheus_client import Counter, Gauge, Histogram
from structlog import get_logger

from authentik.root.celery import CELERY_APP

LOGGER = get_logger()

COUNTER_CELERY_EVENTS = Counter(
    "authentik_system_celery_events_total", "Number of Celery events", ["worker", "type", "task"]
)
HISTOGRAM_TASKS_RUNTIME = Histogram(
    "authentik_system_tasks_runtime_seconds", "Task runtime", ["worker", "task"]
)
GAUGE_TASKS_PREFETCH_TIME = Gauge(
    "authentik_system_tasks_prefetch_time_seconds",
    "Time the task spent waiting at the celery worker to be executed",
    ["worker", "task"],
)
GAUGE_TASKS_WORKER_PREFETCHED = Gauge(
    "authentik_system_tasks_worker_prefetched_tasks",
    "Number of tasks of a given type prefetched at a worker",
    ["worker", "task"],
)
GAUGE_WORKER_ONLINE = Gauge("authentik_system_worker_online", "Worker online status", ["worker"])
GAUGE_WORKER_CURRENTLY_EXECUTING_TASKS = Gauge(
    "authentik_system_worker_currently_executing_tasks",
    "Number of tasks currently executng at a worker",
    ["worker"],
)


class EventsState(State):
    def event(self, event):
        super().event(event)

        worker_name = event["hostname"]
        event_type = event["type"]

        if event_type.startswith("task-"):
            task_id = event["uuid"]
            task = self.tasks.get(task_id)
            task_name = event.get("name", "")
            if not task_name and task_id in self.tasks:
                task_name = task.name or ""
            COUNTER_CELERY_EVENTS.labels(worker=worker_name, type=event_type, task=task_name).inc()

            runtime = event.get("runtime", 0)
            if runtime:
                HISTOGRAM_TASKS_RUNTIME.labels(worker=worker_name, task=task_name).observe(runtime)

            if event_type == "task-received" and not task.eta and task.received:
                GAUGE_TASKS_WORKER_PREFETCHED.labels(worker=worker_name, task=task_name).inc()

            if event_type == "task-started" and not task.eta and task.started and task.received:
                GAUGE_TASKS_PREFETCH_TIME.labels(worker=worker_name, task=task_name).set(
                    task.started - task.received
                )
                GAUGE_TASKS_WORKER_PREFETCHED.labels(worker=worker_name, task=task_name).dec()

            if (
                event_type in ("task-succeeded", "task-failed")
                and not task.eta
                and task.started
                and task.received
            ):
                GAUGE_TASKS_PREFETCH_TIME.labels(worker=worker_name, task=task_name).set(0)

        if event_type in ("worker-online", "worker-heartbeat"):
            GAUGE_WORKER_ONLINE.labels(worker=worker_name).set(1)

        if event_type == "worker-heartbeat":
            executing_tasks = event.get("active")
            if executing_tasks is not None:
                GAUGE_WORKER_CURRENTLY_EXECUTING_TASKS.labels(worker=worker_name).set(
                    executing_tasks
                )

        if event_type == "worker-offline":
            GAUGE_WORKER_ONLINE.labels(worker=worker_name).set(0)


class EventsWatcher:
    events_enable_interval = 5000

    def __init__(self):
        self.state = EventsState()

    def run(self):
        try_interval = 1
        while True:
            CELERY_APP.control.enable_events()
            try:
                try_interval *= 2
                with CELERY_APP.connection() as connection:
                    recv = EventReceiver(connection, handlers={"*": self.on_event}, app=CELERY_APP)
                    try_interval = 1
                    # Every 100 events, start the loop again
                    recv.capture(limit=100, timeout=None, wakeup=True)
            except Exception as exc:
                LOGGER.debug("Failed to receive events", exc=exc)
                sleep(try_interval)

    def on_event(self, event):
        self.state.event(event)
