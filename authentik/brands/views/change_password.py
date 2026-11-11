"""Well-known change password URL"""

from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.http import urlencode
from django.views import View

from authentik.flows.views.executor import NEXT_ARG_NAME
from authentik.stages.password.models import PasswordStage


class ChangePasswordView(View):
    """Redirect to the password stage's configuration flow.

    https://w3c.github.io/webappsec-change-password-url/"""

    def get(self, request: HttpRequest) -> HttpResponse:
        # Same ordering as the user settings API, so this matches the
        # "Change password" button in the user interface.
        stage = PasswordStage.objects.filter(configure_flow__isnull=False).order_by("name").first()
        if not stage:
            raise Http404
        url = reverse("authentik_flows:configure", kwargs={"stage_uuid": stage.pk})
        settings_url = reverse("authentik_core:if-user-path", kwargs={"path": "settings"})
        return redirect(f"{url}?{urlencode({NEXT_ARG_NAME: settings_url})}")
