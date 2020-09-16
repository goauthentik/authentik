"""passbook administration overview"""
from typing import Union

from django.core.cache import cache
from django.shortcuts import redirect, reverse
from django.views.generic import TemplateView
from packaging.version import LegacyVersion, Version, parse
from requests import RequestException, get

from passbook import __version__
from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.models import Application, Provider, Source, User
from passbook.flows.models import Flow, Stage
from passbook.policies.models import Policy
from passbook.root.celery import CELERY_APP
from passbook.stages.invitation.models import Invitation

VERSION_CACHE_KEY = "passbook_latest_version"


def latest_version() -> Union[LegacyVersion, Version]:
    """Get latest release from GitHub, cached"""
    if not cache.get(VERSION_CACHE_KEY):
        try:
            data = get(
                "https://api.github.com/repos/beryju/passbook/releases/latest"
            ).json()
            tag_name = data.get("tag_name")
            cache.set(VERSION_CACHE_KEY, tag_name.split("/")[1], 30)
        except (RequestException, IndexError):
            cache.set(VERSION_CACHE_KEY, "0.0.0", 30)
    return parse(cache.get(VERSION_CACHE_KEY))


class AdministrationOverviewView(AdminRequiredMixin, TemplateView):
    """Overview View"""

    template_name = "administration/overview.html"

    def post(self, *args, **kwargs):
        """Handle post (clear cache from modal)"""
        if "clear" in self.request.POST:
            cache.clear()
            return redirect(reverse("passbook_flows:default-authentication"))
        return self.get(*args, **kwargs)

    def get_context_data(self, **kwargs):
        kwargs["application_count"] = len(Application.objects.all())
        kwargs["policy_count"] = len(Policy.objects.all())
        kwargs["user_count"] = len(User.objects.all()) - 1  # Remove anonymous user
        kwargs["provider_count"] = len(Provider.objects.all())
        kwargs["source_count"] = len(Source.objects.all())
        kwargs["stage_count"] = len(Stage.objects.all())
        kwargs["flow_count"] = len(Flow.objects.all())
        kwargs["invitation_count"] = len(Invitation.objects.all())
        kwargs["version"] = parse(__version__)
        kwargs["version_latest"] = latest_version()
        kwargs["worker_count"] = len(CELERY_APP.control.ping(timeout=0.5))
        kwargs["providers_without_application"] = Provider.objects.filter(
            application=None
        )
        kwargs["policies_without_binding"] = len(
            Policy.objects.filter(bindings__isnull=True, promptstage__isnull=True)
        )
        kwargs["cached_policies"] = len(cache.keys("policy_*"))
        kwargs["cached_flows"] = len(cache.keys("flow_*"))
        return super().get_context_data(**kwargs)
