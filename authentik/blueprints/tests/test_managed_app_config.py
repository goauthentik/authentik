from django.test import TestCase

from authentik.blueprints.apps import ManagedAppConfig
from authentik.enterprise.apps import EnterpriseConfig
from authentik.lib.utils.reflection import get_apps


class TestManagedAppConfig(TestCase):
    def test_apps_use_managed_app_config(self):
        for app in get_apps():
            if app.name.startswith("authentik.enterprise"):
                self.assertIn(EnterpriseConfig, app.__class__.__bases__)
            else:
                self.assertIn(ManagedAppConfig, app.__class__.__bases__)
