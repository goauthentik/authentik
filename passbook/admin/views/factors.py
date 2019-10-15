"""passbook Factor administration"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import \
    PermissionRequiredMixin as DjangoPermissionRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import DeleteView, ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.core.models import Factor
from passbook.lib.utils.reflection import path_to_class
from passbook.lib.views import CreateAssignPermView


def all_subclasses(cls):
    """Recursively return all subclassess of cls"""
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])


class FactorListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all factors"""

    model = Factor
    template_name = 'administration/factor/list.html'
    permission_required = 'passbook_core.view_factor'
    ordering = 'order'
    paginate_by = 40

    def get_context_data(self, **kwargs):
        kwargs['types'] = {
            x.__name__: x._meta.verbose_name for x in all_subclasses(Factor)}
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class FactorCreateView(SuccessMessageMixin, LoginRequiredMixin,
                       DjangoPermissionRequiredMixin, CreateAssignPermView):
    """Create new Factor"""

    model = Factor
    template_name = 'generic/create.html'
    permission_required = 'passbook_core.add_factor'
    permissions = [
        'passbook_core.view_factor',
        'passbook_core.change_factor',
        'passbook_core.delete_factor',
    ]

    success_url = reverse_lazy('passbook_admin:factors')
    success_message = _('Successfully created Factor')

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        factor_type = self.request.GET.get('type')
        model = next(x for x in all_subclasses(Factor) if x.__name__ == factor_type)
        kwargs['type'] = model._meta.verbose_name
        return kwargs

    def get_form_class(self):
        factor_type = self.request.GET.get('type')
        model = next(x for x in all_subclasses(Factor) if x.__name__ == factor_type)
        if not model:
            raise Http404
        return path_to_class(model.form)


class FactorUpdateView(SuccessMessageMixin, LoginRequiredMixin,
                       PermissionRequiredMixin, UpdateView):
    """Update factor"""

    model = Factor
    permission_required = 'passbook_core.update_application'
    template_name = 'generic/update.html'
    success_url = reverse_lazy('passbook_admin:factors')
    success_message = _('Successfully updated Factor')

    def get_form_class(self):
        form_class_path = self.get_object().form
        form_class = path_to_class(form_class_path)
        return form_class

    def get_object(self, queryset=None):
        return Factor.objects.filter(pk=self.kwargs.get('pk')).select_subclasses().first()


class FactorDeleteView(SuccessMessageMixin, LoginRequiredMixin,
                       PermissionRequiredMixin, DeleteView):
    """Delete factor"""

    model = Factor
    template_name = 'generic/delete.html'
    permission_required = 'passbook_core.delete_factor'
    success_url = reverse_lazy('passbook_admin:factors')
    success_message = _('Successfully deleted Factor')

    def get_object(self, queryset=None):
        return Factor.objects.filter(pk=self.kwargs.get('pk')).select_subclasses().first()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
