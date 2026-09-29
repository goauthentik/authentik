"""Test database email template rendering"""

from django.template import TemplateDoesNotExist
from django.test import TestCase

from authentik.lib.generators import generate_id
from authentik.stages.email.models import EmailTemplate


class TestEmailTemplateLoader(TestCase):
    """Test loading EmailTemplates and resolving extends/include"""

    def template(self, body: str, path: str | None = None, managed: bool = False) -> EmailTemplate:
        return EmailTemplate.objects.create(
            path=path or f"{generate_id()}.html",
            body=body,
            managed=generate_id() if managed else None,
        )

    def test_extends(self):
        """Test extending another template by its path"""
        base = self.template("[{% block content %}{% endblock %}]")
        child = self.template(
            f'{{% extends "{base.path}" %}}{{% block content %}}{{{{ name }}}}{{% endblock %}}'
        )
        self.assertEqual(child.render({"name": "child"}), "[child]")

    def test_custom_shadows_managed(self):
        """Test a custom template is used over a managed template with the same path"""
        path = f"{generate_id()}.html"
        self.template("managed {% block content %}{% endblock %}", path=path, managed=True)
        self.template("custom {% block content %}{% endblock %}", path=path)
        child = self.template(f'{{% extends "{path}" %}}{{% block content %}}child{{% endblock %}}')
        self.assertEqual(child.render({}), "custom child")

    def test_custom_extends_shadowed_managed(self):
        """Test a custom template can extend the managed template it shadows"""
        path = f"{generate_id()}.html"
        self.template("managed {% block content %}{% endblock %}", path=path, managed=True)
        self.template(
            f'{{% extends "{path}" %}}{{% block content %}}custom {{% block inner %}}'
            "{% endblock %}{% endblock %}",
            path=path,
        )
        child = self.template(f'{{% extends "{path}" %}}{{% block inner %}}child{{% endblock %}}')
        self.assertEqual(child.render({}), "managed custom child")

    def test_missing_template(self):
        """Test extending a path with no template"""
        child = self.template(f'{{% extends "{generate_id()}.html" %}}')
        with self.assertRaises(TemplateDoesNotExist):
            child.render({})
