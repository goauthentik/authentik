"""email tests"""
from os import chmod, unlink
from pathlib import Path
from tempfile import gettempdir, mkstemp
from typing import Any

from django.conf import settings
from django.test import TestCase

from authentik.stages.email.models import get_template_choices


def get_templates_setting(temp_dir: str) -> dict[str, Any]:
    """Patch settings TEMPLATE's dir property"""
    templates_setting = settings.TEMPLATES
    templates_setting[0]["DIRS"] = [temp_dir]
    return templates_setting


class TestEmailStageTemplates(TestCase):
    """Email tests"""

    def test_custom_template(self):
        """Test with custom template"""
        with self.settings(TEMPLATES=get_templates_setting(gettempdir())):
            _, file = mkstemp(suffix=".html")
            _, file2 = mkstemp(suffix=".html")
            chmod(file2, 0o000)  # Remove all permissions so we can't read the file
            choices = get_template_choices()
            self.assertEqual(choices[-1][0], Path(file).name)
            self.assertEqual(len(choices), 3)
            unlink(file)
            unlink(file2)
