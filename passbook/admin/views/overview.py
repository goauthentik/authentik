"""passbook administration overview"""
from typing import Union

from django.conf import settings
from django.core.cache import cache
from django.db.models import Count
from django.db.models.fields.json import KeyTextTransform
from django.shortcuts import redirect, reverse
from django.views.generic import TemplateView
from packaging.version import LegacyVersion, Version, parse

from passbook import __version__
from passbook.admin.mixins import AdminRequiredMixin
from passbook.admin.tasks import VERSION_CACHE_KEY, update_latest_version
from passbook.audit.models import Event, EventAction
from passbook.core.models import Provider, User
from passbook.policies.models import Policy


class AdministrationOverviewView(AdminRequiredMixin, TemplateView):
    """Overview View"""

    template_name = "administration/overview.html"

    def post(self, *args, **kwargs):
        """Handle post (clear cache from modal)"""
        if "clear" in self.request.POST:
            cache.clear()
            return redirect(reverse("passbook_flows:default-authentication"))
        return self.get(*args, **kwargs)

    def get_latest_version(self) -> Union[LegacyVersion, Version]:
        """Get latest version from cache"""
        version_in_cache = cache.get(VERSION_CACHE_KEY)
        if not version_in_cache:
            if not settings.DEBUG:
                update_latest_version.delay()
            return parse(__version__)
        return parse(version_in_cache)

    def get_most_used_applications(self):
        """Get Most used applications, total login counts and unique users that have used them."""
        return (
            Event.objects.filter(action=EventAction.AUTHORIZE_APPLICATION)
            .exclude(context__authorized_application=None)
            .annotate(application=KeyTextTransform("authorized_application", "context"))
            .annotate(user_pk=KeyTextTransform("pk", "user"))
            .values("application")
            .annotate(total_logins=Count("application"))
            .annotate(unique_users=Count("user_pk", distinct=True))
            .values("unique_users", "application", "total_logins")
            .order_by("-total_logins")[:15]
        )

    def get_context_data(self, **kwargs):
        kwargs["policy_count"] = len(Policy.objects.all())
        kwargs["user_count"] = len(User.objects.all()) - 1  # Remove anonymous user
        kwargs["provider_count"] = len(Provider.objects.all())
        kwargs["version"] = parse(__version__)
        kwargs["version_latest"] = self.get_latest_version()
        kwargs["most_used_applications"] = self.get_most_used_applications()
        kwargs["providers_without_application"] = Provider.objects.filter(
            application=None
        )
        kwargs["policies_without_binding"] = len(
            Policy.objects.filter(bindings__isnull=True, promptstage__isnull=True)
        )
        kwargs["cached_policies"] = len(cache.keys("policy_*"))
        kwargs["cached_flows"] = len(cache.keys("flow_*"))
        return super().get_context_data(**kwargs)
