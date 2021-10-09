"""authentik crypto app config"""
from importlib import import_module

from django.apps import AppConfig


class AuthentikCryptoConfig(AppConfig):
    """authentik crypto app config"""

    name = "authentik.crypto"
    label = "authentik_crypto"
    verbose_name = "authentik Crypto"

    def ready(self):
        import_module("authentik.crypto.managed")
