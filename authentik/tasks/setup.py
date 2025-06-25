import os
from pathlib import Path
from tempfile import gettempdir

from authentik.root.setup import setup

setup()

import django  # noqa: E402

django.setup()

from authentik.root.signals import post_startup, pre_startup, startup  # noqa: E402

_tmp = Path(gettempdir())
prometheus_tmp_dir = str(_tmp.joinpath("authentik_worker_prometheus_tmp"))
os.makedirs(prometheus_tmp_dir, exist_ok=True)
os.environ.setdefault("PROMETHEUS_MULTIPROC_DIR", prometheus_tmp_dir)

_startup_sender = type("WorkerStartup", (object,), {})
pre_startup.send(sender=_startup_sender)
startup.send(sender=_startup_sender)
post_startup.send(sender=_startup_sender)
