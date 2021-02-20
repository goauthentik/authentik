"""admin tests"""
from importlib import import_module
from typing import Callable

from django.forms import ModelForm
from django.test import Client, TestCase
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

from authentik.admin.urls import urlpatterns
from authentik.core.models import Group, User
from authentik.lib.utils.reflection import get_apps


class TestAdmin(TestCase):
    """Generic admin tests"""

    def setUp(self):
        self.user = User.objects.create_user(username="test")
        self.user.ak_groups.add(Group.objects.filter(is_superuser=True).first())
        self.user.save()
        self.client = Client()
        self.client.force_login(self.user)


def generic_view_tester(view_name: str) -> Callable:
    """This is used instead of subTest for better visibility"""

    def tester(self: TestAdmin):
        try:
            full_url = reverse(f"authentik_admin:{view_name}")
            response = self.client.get(full_url)
            self.assertTrue(response.status_code < 500)
        except NoReverseMatch:
            pass

    return tester


for url in urlpatterns:
    method_name = url.name.replace("-", "_")
    setattr(TestAdmin, f"test_view_{method_name}", generic_view_tester(url.name))


def generic_form_tester(form: ModelForm) -> Callable:
    """Test a form"""

    def tester(self: TestAdmin):
        form_inst = form()
        self.assertFalse(form_inst.is_valid())

    return tester


# Load the forms module from every app, so we have all forms loaded
for app in get_apps():
    module = app.__module__.replace(".apps", ".forms")
    try:
        import_module(module)
    except ImportError:
        pass

for form_class in ModelForm.__subclasses__():
    setattr(
        TestAdmin, f"test_form_{form_class.__name__}", generic_form_tester(form_class)
    )
