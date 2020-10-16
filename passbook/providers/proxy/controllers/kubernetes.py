"""Proxy Provider Kubernetes Contoller"""
from passbook.outposts.controllers.kubernetes import KubernetesController
from passbook.outposts.models import Outpost


class ProxyKubernetesController(KubernetesController):
    """Proxy Provider Kubernetes Contoller"""

    def __init__(self, outpost: Outpost):
        super().__init__(outpost)
        self.deployment_ports = {
            "http": 4180,
            "https": 4443,
        }
