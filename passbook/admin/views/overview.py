"""passbook administration overview"""
from django.core.cache import cache
from django.shortcuts import redirect, reverse
from django.views.generic import TemplateView

from passbook import __version__
from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.models import Application, Policy, Provider, Source, User
from passbook.flows.models import Flow, Stage
from passbook.root.celery import CELERY_APP
from passbook.stages.invitation.models import Invitation


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
        kwargs["user_count"] = len(User.objects.all())
        kwargs["provider_count"] = len(Provider.objects.all())
        kwargs["source_count"] = len(Source.objects.all())
        kwargs["stage_count"] = len(Stage.objects.all())
        kwargs["flow_count"] = len(Flow.objects.all())
        kwargs["invitation_count"] = len(Invitation.objects.all())
        kwargs["version"] = __version__
        kwargs["worker_count"] = len(CELERY_APP.control.ping(timeout=0.5))
        kwargs["providers_without_application"] = Provider.objects.filter(
            application=None
        )
        kwargs["policies_without_binding"] = len(
            Policy.objects.filter(policymodel__isnull=True)
        )
        kwargs["cached_policies"] = len(cache.keys("policy_*"))
        return super().get_context_data(**kwargs)
