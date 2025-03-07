"""Enterprise app config"""

from django.conf import settings

from authentik.enterprise.apps import EnterpriseConfig


class AuthentikEnterpriseAuditConfig(EnterpriseConfig):
    """Enterprise app config"""

    name = "authentik.enterprise.audit"
    label = "authentik_audit"
    verbose_name = "authentik Enterprise.Audit"
    default = True

    def ready(self):
        """Install enterprise audit middleware"""
        orig_import = "authentik.events.middleware.AuditMiddleware"
        new_import = "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware"
        settings.MIDDLEWARE = [new_import if x == orig_import else x for x in settings.MIDDLEWARE]
        return super().ready()
