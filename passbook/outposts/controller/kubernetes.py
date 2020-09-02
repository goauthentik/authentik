"""Kubernetes deployment controller"""
from passbook.outposts.models import Outpost


class KubernetesController:

    outpost: Outpost

    def __init__(self, outpost_pk: str):
        self.outpost = Outpost.objects.get(pk=outpost_pk)

    def run(self):
        pass
