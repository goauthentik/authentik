from authentik.root.setup import setup
from authentik.tasks import TASK_WORKER

setup()
TASK_WORKER.enable()

import django  # noqa: E402

django.setup()
