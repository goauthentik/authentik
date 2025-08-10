import os
import sys
from argparse import Namespace

from django.apps.registry import apps
from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string, module_has_submodule
from dramatiq.__main__ import main

from django_dramatiq_postgres.conf import Conf


class Command(BaseCommand):
    """Run worker"""

    def add_arguments(self, parser):
        parser.add_argument(
            "--pid-file",
            action="store",
            default=None,
            dest="pid_file",
            help="PID file",
        )
        parser.add_argument(
            "--watch",
            action="store_true",
            default=False,
            dest="watch",
            help="Watch for file changes",
        )

    def handle(
        self,
        pid_file,
        watch,
        verbosity,
        **options,
    ):
        worker = Conf().worker
        args = Namespace(
            broker="authentik.tasks.setup",
            modules=self._discover_tasks_modules(),
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
        )
        if watch:
            args.watch = worker["watch_folder"]
            if worker["watch_use_polling"]:
                args.watch_use_polling = True

        if processes := worker["processes"]:
            args.processes = processes
        if threads := worker["threads"]:
            args.threads = threads

        if pid_file is not None:
            args.pid_file = pid_file

        args.verbose = verbosity - 1

        main(args)

    def _resolve_executable(self, exec_name: str):
        bin_dir = os.path.dirname(sys.executable)
        if bin_dir:
            for d in [bin_dir, os.path.join(bin_dir, "Scripts")]:
                exec_path = os.path.join(d, exec_name)
                if os.path.isfile(exec_path):
                    return exec_path
        return exec_name

    def _discover_tasks_modules(self) -> list[str]:
        # Does not support a tasks directory
        autodiscovery = Conf().autodiscovery
        modules = [autodiscovery["setup_module"]]

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
        return modules
