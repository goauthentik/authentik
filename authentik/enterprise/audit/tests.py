from django.apps import apps
from django.conf import settings
from django.test import TestCase


class TestEnterpriseAudit(TestCase):

    def test_import(self):
        """Ensure middleware is imported when app.ready is called"""
        # Revert import swap
        orig_import = "authentik.events.middleware.AuditMiddleware"
        new_import = "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware"
        settings.MIDDLEWARE = [orig_import if x == new_import else x for x in settings.MIDDLEWARE]
        # Re-call ready()
        apps.get_app_config("authentik_enterprise_audit").ready()
        self.assertIn(
            "authentik.enterprise.audit.middleware.EnterpriseAuditMiddleware", settings.MIDDLEWARE
        )
