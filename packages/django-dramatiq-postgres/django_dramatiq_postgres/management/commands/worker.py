import sys
from argparse import Namespace
from typing import Any

from django.apps.registry import apps
from django.core.management.base import BaseCommand, CommandParser
from django.db import connections
from django.utils.module_loading import import_string, module_has_submodule
from dramatiq.cli import main

from django_dramatiq_postgres.conf import Conf


class Command(BaseCommand):
    """Run worker"""

    def add_arguments(self, parser: CommandParser) -> None:
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
        pid_file: str,
        watch: bool,
        verbosity: int,
        **options: Any,
    ) -> None:
        worker = Conf().worker
        setup, modules = self._discover_tasks_modules()
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

        connections.close_all()
        sys.exit(main(args))  # type: ignore[no-untyped-call]

    def _discover_tasks_modules(self) -> tuple[str, list[str]]:
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
