from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView

from passbook.core.models import Application, Rule, User


class AdministrationOverviewView(LoginRequiredMixin, TemplateView):

    template_name = 'administration/overview.html'

    def get_context_data(self, **kwargs):
        kwargs['application_count'] = len(Application.objects.all())
        kwargs['rule_count'] = len(Rule.objects.all())
        kwargs['user_count'] = len(User.objects.all())
        return super().get_context_data(**kwargs)
