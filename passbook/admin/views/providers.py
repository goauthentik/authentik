"""passbook Provider administration"""
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.models import Provider
from passbook.lib.utils.reflection import path_to_class


class ProviderListView(AdminRequiredMixin, ListView):
    """Show list of all providers"""

    model = Provider
    template_name = 'administration/provider/list.html'

    def get_context_data(self, **kwargs):
        kwargs['types'] = {
            x.__name__: x._meta.verbose_name for x in Provider.__subclasses__()}
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class ProviderCreateView(SuccessMessageMixin, AdminRequiredMixin, CreateView):
    """Create new Provider"""

    template_name = 'generic/create_inheritance.html'
    success_url = reverse_lazy('passbook_admin:providers')
    success_message = _('Successfully created Provider')

    def get_form_class(self):
        provider_type = self.request.GET.get('type')
        model = next(x for x in Provider.__subclasses__()
                     if x.__name__ == provider_type)
        if not model:
            raise Http404
        return path_to_class(model.form)


class ProviderUpdateView(SuccessMessageMixin, AdminRequiredMixin, UpdateView):
    """Update provider"""

    model = Provider
    template_name = 'generic/update.html'
    success_url = reverse_lazy('passbook_admin:providers')
    success_message = _('Successfully updated Provider')

    def get_form_class(self):
        form_class_path = self.get_object().form
        form_class = path_to_class(form_class_path)
        return form_class

    def get_object(self, queryset=None):
        return Provider.objects.filter(pk=self.kwargs.get('pk')).select_subclasses().first()


class ProviderDeleteView(SuccessMessageMixin, AdminRequiredMixin, DeleteView):
    """Delete provider"""

    model = Provider
    template_name = 'generic/delete.html'
    success_url = reverse_lazy('passbook_admin:providers')
    success_message = _('Successfully updated Provider')

    def get_object(self, queryset=None):
        return Provider.objects.filter(pk=self.kwargs.get('pk')).select_subclasses().first()
