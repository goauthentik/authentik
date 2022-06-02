"""authentik benchmark command"""
from csv import DictWriter
from multiprocessing import Manager, cpu_count, get_context
from sys import stdout
from time import time

from django import db
from django.core.management.base import BaseCommand
from django.test import RequestFactory
from structlog.stdlib import get_logger

from authentik import __version__
from authentik.core.tests.utils import create_test_admin_user
from authentik.flows.models import Flow
from authentik.flows.planner import PLAN_CONTEXT_PENDING_USER, FlowPlanner

LOGGER = get_logger()
FORK_CTX = get_context("fork")
PROCESS_CLASS = FORK_CTX.Process


class FlowPlanProcess(PROCESS_CLASS):  # pragma: no cover
    """Test process which executes flow planner"""

    def __init__(self, index, return_dict, flow, user) -> None:
        super().__init__()
        self.index = index
        self.return_dict = return_dict
        self.flow = flow
        self.user = user
        self.request = RequestFactory().get("/")

    def run(self):
        """Execute 1000 flow plans"""
        print(f"Proc {self.index} Running")

        def test_inner():
            planner = FlowPlanner(self.flow)
            planner.use_cache = False
            planner.plan(self.request, {PLAN_CONTEXT_PENDING_USER: self.user})

        diffs = []
        for _ in range(1000):
            start = time()
            test_inner()
            end = time()
            diffs.append(end - start)
        self.return_dict[self.index] = diffs


class Command(BaseCommand):  # pragma: no cover
    """Benchmark authentik"""

    def add_arguments(self, parser):
        parser.add_argument(
            "-p",
            "--processes",
            default=cpu_count(),
            action="store",
            help="How many processes should be started.",
        )
        parser.add_argument(
            "--csv",
            action="store_true",
            help="Output results as CSV",
        )

    def benchmark_flows(self, proc_count):
        """Get full recovery link"""
        flow = Flow.objects.get(slug="default-authentication-flow")
        user = create_test_admin_user()
        manager = Manager()
        return_dict = manager.dict()

        jobs = []
        db.connections.close_all()
        for i in range(proc_count):
            proc = FlowPlanProcess(i, return_dict, flow, user)
            jobs.append(proc)
            proc.start()

        for proc in jobs:
            proc.join()
        return return_dict.values()

    def handle(self, *args, **options):
        """Start benchmark"""
        proc_count = options.get("processes", 1)
        all_values = self.benchmark_flows(proc_count)
        if options.get("csv"):
            self.output_csv(all_values)
        else:
            self.output_overview(all_values)

    def output_overview(self, values):
        """Output results human readable"""
        total_max: int = max(max(inner) for inner in values)
        total_min: int = min(min(inner) for inner in values)
        total_avg = sum(sum(inner) for inner in values) / sum(len(inner) for inner in values)

        print(f"Version: {__version__}")
        print(f"Processes: {len(values)}")
        print(f"\tMax: {total_max * 100}ms")
        print(f"\tMin: {total_min * 100}ms")
        print(f"\tAvg: {total_avg * 100}ms")

    def output_csv(self, values):
        """Output results as CSV"""
        proc_count = len(values)
        fieldnames = [f"proc_{idx}" for idx in range(proc_count)]
        writer = DictWriter(stdout, fieldnames=fieldnames)

        writer.writeheader()
        for run_idx in range(len(values[0])):
            row_dict = {}
            for proc_idx in range(proc_count):
                row_dict[f"proc_{proc_idx}"] = values[proc_idx][run_idx] * 100
            writer.writerow(row_dict)
