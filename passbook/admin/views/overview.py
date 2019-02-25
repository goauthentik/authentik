"""passbook administration overview"""
from django.views.generic import TemplateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core import __version__
from passbook.core.celery import CELERY_APP
from passbook.core.models import (Application, Factor, Invitation, Policy,
                                  Provider, Source, User)


class AdministrationOverviewView(AdminRequiredMixin, TemplateView):
    """Overview View"""

    template_name = 'administration/overview.html'

    def get_context_data(self, **kwargs):
        kwargs['application_count'] = len(Application.objects.all())
        kwargs['policy_count'] = len(Policy.objects.all())
        kwargs['user_count'] = len(User.objects.all())
        kwargs['provider_count'] = len(Provider.objects.all())
        kwargs['source_count'] = len(Source.objects.all())
        kwargs['factor_count'] = len(Factor.objects.all())
        kwargs['invitation_count'] = len(Invitation.objects.all())
        kwargs['version'] = __version__
        kwargs['worker_count'] = len(CELERY_APP.control.ping(timeout=0.5))
        return super().get_context_data(**kwargs)
