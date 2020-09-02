"""Proxy Provider Kubernetes Contoller"""
from passbook.outposts.controllers.kubernetes import KubernetesController


class ProxyKubernetesController(KubernetesController):
    """Proxy Provider Kubernetes Contoller"""

    def __init__(self, outpost_pk: str):
        super().__init__(outpost_pk)
        self.deployment_ports = {
            "http": 4180,
            "https": 4443,
        }
