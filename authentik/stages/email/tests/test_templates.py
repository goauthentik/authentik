"""email tests"""
from os import unlink
from pathlib import Path
from sys import platform
from tempfile import gettempdir, mkstemp
from typing import Any
from unittest.case import skipUnless

from django.conf import settings
from django.test import TestCase

from authentik.stages.email.models import get_template_choices


def get_templates_setting(temp_dir: str) -> dict[str, Any]:
    """Patch settings TEMPLATE's dir property"""
    templates_setting = settings.TEMPLATES
    templates_setting[0]["DIRS"] = [temp_dir]
    return templates_setting


@skipUnless(platform.startswith("linux"), "requires local docker")
class TestEmailStageTemplates(TestCase):
    """Email tests"""

    def test_custom_template(self):
        """Test with custom template"""
        with self.settings(TEMPLATES=get_templates_setting(gettempdir())):
            _, file = mkstemp(suffix=".html")
            self.assertEqual(get_template_choices()[-1][0], Path(file).name)
            unlink(file)
