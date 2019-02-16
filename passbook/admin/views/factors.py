"""passbook Factor administration"""
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.forms.factor import FactorForm
from passbook.core.models import Factor


class FactorListView(AdminRequiredMixin, ListView):
    """Show list of all factors"""

    model = Factor
    template_name = 'administration/factor/list.html'
    ordering = 'order'

    def get_context_data(self, **kwargs):
        kwargs['types'] = {
            x.__name__: x._meta.verbose_name for x in Factor.__subclasses__()}
        return super().get_context_data(**kwargs)


class FactorCreateView(SuccessMessageMixin, AdminRequiredMixin, CreateView):
    """Create new Factor"""

    template_name = 'generic/create.html'
    success_url = reverse_lazy('passbook_admin:factors')
    success_message = _('Successfully created Factor')
    form_class = FactorForm


class FactorUpdateView(SuccessMessageMixin, AdminRequiredMixin, UpdateView):
    """Update factor"""

    model = Factor
    template_name = 'generic/update.html'
    success_url = reverse_lazy('passbook_admin:factors')
    success_message = _('Successfully updated Factor')
    form_class = FactorForm


class FactorDeleteView(SuccessMessageMixin, AdminRequiredMixin, DeleteView):
    """Delete factor"""

    model = Factor
    template_name = 'generic/delete.html'
    success_url = reverse_lazy('passbook_admin:factors')
    success_message = _('Successfully updated Factor')
