"""Authenticator"""

from django.db.models.signals import post_save, pre_delete

from authentik.blueprints.apps import ManagedAppConfig
from authentik.stages.authenticator import device_classes


class AuthentikStageAuthenticatorConfig(ManagedAppConfig):
    """Authenticator App config"""

    name = "authentik.stages.authenticator"
    label = "authentik_stages_authenticator"
    verbose_name = "authentik Stages.Authenticator"
    default = True

    def ready(self):
        from authentik.stages.authenticator.signals import (
            device_post_save_event,
            device_pre_delete_event,
        )

        for model in device_classes():
            post_save.connect(
                device_post_save_event,
                sender=model,
                dispatch_uid=f"ak_mfa_added_{model._meta.label}",
            )
            pre_delete.connect(
                device_pre_delete_event,
                sender=model,
                dispatch_uid=f"ak_mfa_removed_{model._meta.label}",
            )
