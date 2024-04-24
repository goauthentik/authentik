import collections
import shelve
import threading

from celery.events import EventReceiver
from celery.events.state import State
from prometheus_client import Counter, Gauge, Histogram

PROMETHEUS_METRICS = None


def get_prometheus_metrics():
    global PROMETHEUS_METRICS
    if PROMETHEUS_METRICS is None:
        PROMETHEUS_METRICS = PrometheusMetrics()
    return PROMETHEUS_METRICS


class PrometheusMetrics:
    def __init__(self):
        self.events = Counter(
            "authentik_celery_events_total", "Number of Celery events", ["worker", "type", "task"]
        )
        self.runtime = Histogram(
            "authentik_tasks_runtime_seconds", "Task runtime", ["worker", "task"]
        )
        self.prefetch_time = Gauge(
            "authentik_tasks_prefetch_time_seconds",
            "Time the task spent waiting at the celery worker to be executed",
            ["worker", "task"],
        )
        self.prefetched_tasks = Gauge(
            "authentik_tasks_worker_prefetched_tasks",
            "Number of tasks of a given type prefetched at a worker",
            ["worker", "task"],
        )
        self.worker_online = Gauge("authentik_worker_online", "Worker online status", ["worker"])
        self.worker_currently_executing_tasks = Gauge(
            "authentik_worker_currently_executing_tasks",
            "Number of tasks currently executng at a worker",
            ["worker"],
        )


class EventsState(State):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.counter = collections.defaultdict(collections.Counter)
        self.metrics = get_prometheus_metrics()

    def event(self, event):
        super().event(event)

        worker_name = event["hostname"]
        event_type = event["type"]

        self.counter[worker_name][event_type] += 1

        if event_type.startswith("task-"):
            task_id = event["uuid"]
            task = self.tasks.get(task_id)
            task_name = event.get("name", "")
            if not task_name and task_id in self.tasks:
                task_name = task.name or ""
            self.metrics.events.labels(worker=worker_name, type=event_type, task=task_name).inc()

            runtime = event.get("runtime", 0)
            if runtime:
                self.metrics.runtime.labels(worker=worker_name, task=task_name).observe(runtime)

            if event_type == "task-received" and not task.eta and task.received:
                self.metrics.prefetched_tasks.labels(worker=worker_name, task=task_name).inc()

            if event_type == "task-started" and not task.eta and task.started and task.received:
                self.metrics.prefetch_time.labels(worker=worker_name, task=task_name).set(
                    task.started - task.received
                )
                self.metrics.prefetched_tasks.labels(worker=worker_name, task=task_name).dec()

            if (
                event_type in ("task-succeeded", "task-failed")
                and not task.eta
                and task.started
                and task.received
            ):
                self.metrics.prefetch_time.labels(worker=worker_name, task=task_name).set(0)

        if event_type in ("worker-online", "worker-heartbeat"):
            self.metrics.worker_online.labels(worker=worker_name).set(1)

        if event_type == "worker-heartbeat":
            executing_tasks = event.get("active")
            if executing_tasks is not None:
                self.metrics.worker_currently_executing_tasks.labels(worker=worker_name).set(
                    executing_tasks
                )

        if event_type == "worker-offline":
            self.metrics.worker_online.labels(worker=worker_name).set(0)


class Events(threading.Thread):
    events_enable_interval = 5000

    def __init__(
        self,
        capp,
        io_loop,
        db=None,
        persistent=False,
        enable_events=True,
        state_save_interval=0,
        **kwargs,
    ):
        threading.Thread.__init__(self)
        self.daemon = True

        self.io_loop = io_loop
        self.capp = capp

        self.db = db
        self.persistent = persistent
        self.enable_events = enable_events
        self.state = None
        self.state_save_time = None

        if self.persistent:
            state = shelve.open(self.db)
