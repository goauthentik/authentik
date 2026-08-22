"""exceptions used by the kubernetes reconciler to trigger updates"""

from authentik.lib.tracing import TracingIgnoredException


class ReconcileTrigger(TracingIgnoredException):
    """Base trigger raised by child classes to notify us"""


class NeedsRecreate(ReconcileTrigger):
    """Exception to trigger a complete recreate of the Kubernetes Object"""


class NeedsUpdate(ReconcileTrigger):
    """Exception to trigger an update to the Kubernetes Object"""
