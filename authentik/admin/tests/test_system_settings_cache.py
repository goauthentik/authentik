from django.http import HttpRequest, HttpResponse
from django.test import RequestFactory, TestCase

from authentik.admin.middleware import SystemSettingsCacheRequestMiddleware
from authentik.admin.models import SystemSettings
from authentik.admin.utils import get_system_settings


class TestSystemSettingsCache(TestCase):
    def test_scoped_to_request(self):
        """Settings are only cached within a single request"""
        seen = []

        def view(request: HttpRequest) -> HttpResponse:
            seen.extend([get_system_settings(), get_system_settings()])
            return HttpResponse()

        middleware = SystemSettingsCacheRequestMiddleware(view)
        middleware(RequestFactory().get("/"))
        middleware(RequestFactory().get("/"))
        self.assertIs(seen[0], seen[1])
        self.assertIsNot(seen[1], seen[2])
        self.assertIs(seen[2], seen[3])
        self.assertIsNot(get_system_settings(), get_system_settings())

    def test_fresh_outside_requests(self):
        """System settings cache is not used outside of a request"""
        first = get_system_settings()
        SystemSettings.objects.filter(pk=True).update(avatars="none")
        second = get_system_settings()
        self.assertIsNot(first, second)
        self.assertEqual(second.avatars, "none")
