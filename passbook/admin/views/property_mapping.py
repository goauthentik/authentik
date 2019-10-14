"""passbook PropertyMapping administration"""
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import CreateView, DeleteView, ListView, UpdateView

from passbook.admin.mixins import AdminRequiredMixin
from passbook.core.models import PropertyMapping
from passbook.lib.utils.reflection import path_to_class


def all_subclasses(cls):
    """Recursively return all subclassess of cls"""
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])


class PropertyMappingListView(AdminRequiredMixin, ListView):
    """Show list of all property_mappings"""

    model = PropertyMapping
    template_name = 'administration/property_mapping/list.html'
    ordering = 'name'
    paginate_by = 40

    def get_context_data(self, **kwargs):
        kwargs['types'] = {
            x.__name__: x._meta.verbose_name for x in all_subclasses(PropertyMapping)}
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class PropertyMappingCreateView(SuccessMessageMixin, AdminRequiredMixin, CreateView):
    """Create new PropertyMapping"""

    template_name = 'generic/create.html'
    success_url = reverse_lazy('passbook_admin:property-mappings')
    success_message = _('Successfully created Property Mapping')

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        property_mapping_type = self.request.GET.get('type')
        model = next(x for x in all_subclasses(PropertyMapping)
                     if x.__name__ == property_mapping_type)
        kwargs['type'] = model._meta.verbose_name
        return kwargs

    def get_form_class(self):
        property_mapping_type = self.request.GET.get('type')
        model = next(x for x in all_subclasses(PropertyMapping)
                     if x.__name__ == property_mapping_type)
        if not model:
            raise Http404
        return path_to_class(model.form)


class PropertyMappingUpdateView(SuccessMessageMixin, AdminRequiredMixin, UpdateView):
    """Update property_mapping"""

    model = PropertyMapping
    template_name = 'generic/update.html'
    success_url = reverse_lazy('passbook_admin:property-mappings')
    success_message = _('Successfully updated Property Mapping')

    def get_form_class(self):
        form_class_path = self.get_object().form
        form_class = path_to_class(form_class_path)
        return form_class

    def get_object(self, queryset=None):
        return PropertyMapping.objects.filter(pk=self.kwargs.get('pk')).select_subclasses().first()


class PropertyMappingDeleteView(SuccessMessageMixin, AdminRequiredMixin, DeleteView):
    """Delete property_mapping"""

    model = PropertyMapping
    template_name = 'generic/delete.html'
    success_url = reverse_lazy('passbook_admin:property-mappings')
    success_message = _('Successfully deleted Property Mapping')

    def get_object(self, queryset=None):
        return PropertyMapping.objects.filter(pk=self.kwargs.get('pk')).select_subclasses().first()

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
