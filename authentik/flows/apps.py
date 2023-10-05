"""authentik flows app config"""
from prometheus_client import Gauge, Histogram

from authentik.blueprints.apps import ManagedAppConfig
from authentik.lib.utils.reflection import all_subclasses

GAUGE_FLOWS_CACHED = Gauge(
    "authentik_flows_cached",
    "Cached flows",
)
HIST_FLOW_EXECUTION_STAGE_TIME = Histogram(
    "authentik_flows_execution_stage_time",
    "Duration each stage took to execute.",
    ["stage_type", "method"],
)
HIST_FLOWS_PLAN_TIME = Histogram(
    "authentik_flows_plan_time",
    "Duration to build a plan for a flow",
    ["flow_slug"],
)


class AuthentikFlowsConfig(ManagedAppConfig):
    """authentik flows app config"""

    name = "authentik.flows"
    label = "authentik_flows"
    mountpoint = "flows/"
    verbose_name = "authentik Flows"
    default = True

    def reconcile_load_flows_signals(self):
        """Load flows signals"""
        self.import_module("authentik.flows.signals")

    def reconcile_load_stages(self):
        """Ensure all stages are loaded"""
        from authentik.flows.models import Stage

        for stage in all_subclasses(Stage):
            _ = stage().type
