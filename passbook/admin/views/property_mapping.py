"""passbook PropertyMapping administration"""
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import Http404
from django.urls import reverse_lazy
from django.utils.translation import ugettext as _
from django.views.generic import DeleteView, ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.core.models import PropertyMapping
from passbook.lib.utils.reflection import all_subclasses, path_to_class
from passbook.lib.views import CreateAssignPermView


class PropertyMappingListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all property_mappings"""

    model = PropertyMapping
    permission_required = "passbook_core.view_propertymapping"
    template_name = "administration/property_mapping/list.html"
    ordering = "name"
    paginate_by = 40

    def get_context_data(self, **kwargs):
        kwargs["types"] = {
            x.__name__: x for x in all_subclasses(PropertyMapping)
        }
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class PropertyMappingCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new PropertyMapping"""

    model = PropertyMapping
    permission_required = "passbook_core.add_propertymapping"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:property-mappings")
    success_message = _("Successfully created Property Mapping")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        property_mapping_type = self.request.GET.get("type")
        try:
            model = next(
                x
                for x in all_subclasses(PropertyMapping)
                if x.__name__ == property_mapping_type
            )
        except StopIteration as exc:
            raise Http404 from exc
        kwargs["type"] = model._meta.verbose_name
        form_cls = self.get_form_class()
        if hasattr(form_cls, "template_name"):
            kwargs["base_template"] = form_cls.template_name
        return kwargs

    def get_form_class(self):
        property_mapping_type = self.request.GET.get("type")
        try:
            model = next(
                x
                for x in all_subclasses(PropertyMapping)
                if x.__name__ == property_mapping_type
            )
        except StopIteration as exc:
            raise Http404 from exc
        return path_to_class(model.form)


class PropertyMappingUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update property_mapping"""

    model = PropertyMapping
    permission_required = "passbook_core.change_propertymapping"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:property-mappings")
    success_message = _("Successfully updated Property Mapping")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        form_cls = self.get_form_class()
        if hasattr(form_cls, "template_name"):
            kwargs["base_template"] = form_cls.template_name
        return kwargs

    def get_form_class(self):
        form_class_path = self.get_object().form
        form_class = path_to_class(form_class_path)
        return form_class

    def get_object(self, queryset=None):
        return (
            PropertyMapping.objects.filter(pk=self.kwargs.get("pk"))
            .select_subclasses()
            .first()
        )


class PropertyMappingDeleteView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete property_mapping"""

    model = PropertyMapping
    permission_required = "passbook_core.delete_propertymapping"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:property-mappings")
    success_message = _("Successfully deleted Property Mapping")

    def get_object(self, queryset=None):
        return (
            PropertyMapping.objects.filter(pk=self.kwargs.get("pk"))
            .select_subclasses()
            .first()
        )

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
