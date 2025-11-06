from argparse import Namespace
from pathlib import Path
from tempfile import gettempdir

from django.apps.registry import apps
from django.utils.module_loading import import_string, module_has_submodule
from django_dramatiq_postgres.conf import Conf


def _discover_tasks_modules() -> tuple[str, list[str]]:
    # Does not support a tasks directory
    autodiscovery = Conf().autodiscovery
    modules = []

    if autodiscovery["enabled"]:
        for app in apps.get_app_configs():
            if autodiscovery["apps_prefix"] and not app.name.startswith(
                autodiscovery["apps_prefix"]
            ):
                continue
            if module_has_submodule(app.module, autodiscovery["actors_module_name"]):
                modules.append(f"{app.name}.{autodiscovery['actors_module_name']}")
    else:
        modules_callback = autodiscovery["modules_callback"]
        callback = (
            modules_callback
            if not isinstance(modules_callback, str)
            else import_string(modules_callback)
        )
        modules.extend(callback())
    return autodiscovery["setup_module"], modules


tmp = Path(gettempdir())
worker = Conf().worker
setup, modules = _discover_tasks_modules()
args = Namespace(
    broker=setup,
    modules=modules,
    path=["."],
    queues=None,
    log_file=None,
    skip_logging=True,
    use_spawn=False,
    forks=[],
    worker_shutdown_timeout=600000,
    watch=None,
    watch_use_polling=False,
    include_patterns=["**.py"],
    exclude_patterns=None,
    verbose=0,
    pid_file=str(tmp / "authentik-worker.pid"),
)

if processes := worker["processes"]:
    args.processes = processes
if threads := worker["threads"]:
    args.threads = threads
