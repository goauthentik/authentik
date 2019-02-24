"""passbook Factor administration"""
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.models import Factor
from passbook.lib.utils.reflection import path_to_class


def all_subclasses(cls):
    """Recursively return all subclassess of cls"""
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])

class FactorListView(AdminRequiredMixin, ListView):
    """Show list of all factors"""

    model = Factor
    template_name = 'administration/factor/list.html'
    ordering = 'order'

    def get_context_data(self, **kwargs):
        kwargs['types'] = {
            x.__name__: x._meta.verbose_name for x in all_subclasses(Factor)}
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().select_subclasses()

class FactorCreateView(SuccessMessageMixin, AdminRequiredMixin, CreateView):
    """Create new Factor"""

    template_name = 'generic/create_inheritance.html'
    success_url = reverse_lazy('passbook_admin:factors')
    success_message = _('Successfully created Factor')

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        source_type = self.request.GET.get('type')
        model = next(x for x in all_subclasses(Factor) if x.__name__ == source_type)
        kwargs['type'] = model._meta.verbose_name
        return kwargs

    def get_form_class(self):
        source_type = self.request.GET.get('type')
        model = next(x for x in all_subclasses(Factor) if x.__name__ == source_type)
        if not model:
            raise Http404
        return path_to_class(model.form)


class FactorUpdateView(SuccessMessageMixin, AdminRequiredMixin, UpdateView):
    """Update factor"""

    model = Factor
    template_name = 'generic/update.html'
    success_url = reverse_lazy('passbook_admin:factors')
    success_message = _('Successfully updated Factor')

    def get_form_class(self):
        source_type = self.request.GET.get('type')
        model = next(x for x in all_subclasses(Factor) if x.__name__ == source_type)
        if not model:
            raise Http404
        return path_to_class(model.form)

class FactorDeleteView(SuccessMessageMixin, AdminRequiredMixin, DeleteView):
    """Delete factor"""

    model = Factor
    template_name = 'generic/delete.html'
    success_url = reverse_lazy('passbook_admin:factors')
    success_message = _('Successfully updated Factor')

    def get_object(self, queryset=None):
        return Factor.objects.filter(pk=self.kwargs.get('pk')).select_subclasses().first()
