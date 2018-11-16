"""passbook administration overview"""
from django.views.generic import TemplateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.models import Application, Provider, Rule, User


class AdministrationOverviewView(AdminRequiredMixin, TemplateView):
    """Overview View"""

    template_name = 'administration/overview.html'

    def get_context_data(self, **kwargs):
        kwargs['application_count'] = len(Application.objects.all())
        kwargs['rule_count'] = len(Rule.objects.all())
        kwargs['user_count'] = len(User.objects.all())
        kwargs['provider_count'] = len(Provider.objects.all())
        return super().get_context_data(**kwargs)
