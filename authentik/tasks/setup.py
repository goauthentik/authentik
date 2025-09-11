from authentik.root.setup import setup

setup()

import django  # noqa: E402

django.setup()

from authentik.root.signals import post_startup, pre_startup, startup  # noqa: E402

_startup_sender = type("WorkerStartup", (object,), {})
pre_startup.send(sender=_startup_sender)
startup.send(sender=_startup_sender)
post_startup.send(sender=_startup_sender)
