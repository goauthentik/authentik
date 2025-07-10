import os
import sys

from django.apps.registry import apps
from django.core.management.base import BaseCommand
from django.utils.module_loading import import_string, module_has_submodule

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
        executable_name = "dramatiq-gevent" if worker["use_gevent"] else "dramatiq"
        executable_path = self._resolve_executable(executable_name)
        watch_args = ["--watch", worker["watch_folder"]] if watch else []
        if watch_args and worker["watch_use_polling"]:
            watch_args.append("--watch-use-polling")

        parallel_args = []
        if processes := worker["processes"]:
            parallel_args.extend(["--processes", str(processes)])
        if threads := worker["threads"]:
            parallel_args.extend(["--threads", str(threads)])

        pid_file_args = []
        if pid_file is not None:
            pid_file_args = ["--pid-file", pid_file]

        verbosity_args = ["-v"] * (verbosity - 1)

        tasks_modules = self._discover_tasks_modules()
        process_args = [
            executable_name,
            "--path",
            ".",
            *parallel_args,
            *watch_args,
            *pid_file_args,
            *verbosity_args,
            *tasks_modules,
        ]

        os.execvp(executable_path, process_args)  # nosec

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
