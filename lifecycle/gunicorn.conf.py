"""Gunicorn config"""
import os
from hashlib import sha512
from multiprocessing import cpu_count
from os import makedirs
from pathlib import Path
from tempfile import gettempdir
from typing import TYPE_CHECKING

from kubernetes.config.incluster_config import SERVICE_HOST_ENV_NAME
from prometheus_client.values import MultiProcessValue

from authentik import get_full_version
from authentik.lib.config import CONFIG
from authentik.lib.logging import get_logger_config
from authentik.lib.utils.http import get_http_session
from authentik.lib.utils.reflection import get_env
from authentik.root.install_id import get_install_id_raw
from lifecycle.worker import DjangoUvicornWorker

if TYPE_CHECKING:
    from gunicorn.arbiter import Arbiter

_tmp = Path(gettempdir())
worker_class = "lifecycle.worker.DjangoUvicornWorker"
worker_tmp_dir = str(_tmp.joinpath("authentik_worker_tmp"))
prometheus_tmp_dir = str(_tmp.joinpath("authentik_prometheus_tmp"))

makedirs(worker_tmp_dir, exist_ok=True)
makedirs(prometheus_tmp_dir, exist_ok=True)

bind = f"unix://{str(_tmp.joinpath('authentik-core.sock'))}"

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "authentik.root.settings")
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", prometheus_tmp_dir)

max_requests = 1000
max_requests_jitter = 50

logconfig_dict = get_logger_config()

# if we're running in kubernetes, use fixed workers because we can scale with more pods
# otherwise (assume docker-compose), use as much as we can
if SERVICE_HOST_ENV_NAME in os.environ:
    default_workers = 2
else:
    default_workers = max(cpu_count() * 0.25, 1) + 1  # Minimum of 2 workers

workers = CONFIG.get_int("web.workers", default_workers)
threads = CONFIG.get_int("web.threads", 4)


def post_fork(server: "Arbiter", worker: DjangoUvicornWorker):
    """Tell prometheus to use worker number instead of process ID for multiprocess"""
    from prometheus_client import values

    values.ValueClass = MultiProcessValue(lambda: worker._worker_id)


def worker_exit(server: "Arbiter", worker: DjangoUvicornWorker):
    """Remove pid dbs when worker is shutdown"""
    from prometheus_client import multiprocess

    multiprocess.mark_process_dead(worker._worker_id)


def on_starting(server: "Arbiter"):
    """Attach a set of IDs that can be temporarily reused.
    Used on reloads when each worker exists twice."""
    server._worker_id_overload = set()


def nworkers_changed(server: "Arbiter", new_value, old_value):
    """Gets called on startup too.
    Set the current number of workers.  Required if we raise the worker count
    temporarily using TTIN because server.cfg.workers won't be updated and if
    one of those workers dies, we wouldn't know the ids go that far."""
    server._worker_id_current_workers = new_value


def _next_worker_id(server: "Arbiter"):
    """If there are IDs open for reuse, take one.  Else look for a free one."""
    if server._worker_id_overload:
        return server._worker_id_overload.pop()

    in_use = set(w._worker_id for w in tuple(server.WORKERS.values()) if w.alive)
    free = set(range(1, server._worker_id_current_workers + 1)) - in_use

    return free.pop()


def on_reload(server: "Arbiter"):
    """Add a full set of ids into overload so it can be reused once."""
    server._worker_id_overload = set(range(1, server.cfg.workers + 1))


def pre_fork(server: "Arbiter", worker: DjangoUvicornWorker):
    """Attach the next free worker_id before forking off."""
    worker._worker_id = _next_worker_id(server)


if not CONFIG.get_bool("disable_startup_analytics", False):
    env = get_env()
    should_send = env not in ["dev", "ci"]
    if should_send:
        try:
            get_http_session().post(
                "https://goauthentik.io/api/event",
                json={
                    "domain": "authentik",
                    "name": "pageview",
                    "referrer": get_full_version(),
                    "url": (
                        f"http://localhost/{env}?utm_source={get_full_version()}&utm_medium={env}"
                    ),
                },
                headers={
                    "User-Agent": sha512(get_install_id_raw().encode("ascii")).hexdigest()[:16],
                    "Content-Type": "application/json",
                },
                timeout=5,
            )
        # pylint: disable=broad-exception-caught
        except Exception:  # nosec
            pass

if CONFIG.get_bool("remote_debug"):
    import debugpy

    debugpy.listen(("0.0.0.0", 6800))  # nosec
