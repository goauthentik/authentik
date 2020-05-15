"""passbook Inlet administration"""
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

from passbook.core.models import Inlet
from passbook.lib.utils.reflection import all_subclasses, path_to_class
from passbook.lib.views import CreateAssignPermView


class InletListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all inlets"""

    model = Inlet
    permission_required = "passbook_core.view_inlet"
    ordering = "name"
    paginate_by = 40
    template_name = "administration/inlet/list.html"

    def get_context_data(self, **kwargs):
        kwargs["types"] = {
            x.__name__: x._meta.verbose_name for x in all_subclasses(Inlet)
        }
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class InletCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Inlet"""

    model = Inlet
    permission_required = "passbook_core.add_inlet"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:inlets")
    success_message = _("Successfully created Inlet")

    def get_form_class(self):
        inlet_type = self.request.GET.get("type")
        model = next(x for x in all_subclasses(Inlet) if x.__name__ == inlet_type)
        if not model:
            raise Http404
        return path_to_class(model.form)


class InletUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update inlet"""

    model = Inlet
    permission_required = "passbook_core.change_inlet"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:inlets")
    success_message = _("Successfully updated Inlet")

    def get_form_class(self):
        form_class_path = self.get_object().form
        form_class = path_to_class(form_class_path)
        return form_class

    def get_object(self, queryset=None):
        return (
            Inlet.objects.filter(pk=self.kwargs.get("pk")).select_subclasses().first()
        )


class InletDeleteView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete inlet"""

    model = Inlet
    permission_required = "passbook_core.delete_inlet"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:inlets")
    success_message = _("Successfully deleted Inlet")

    def get_object(self, queryset=None):
        return (
            Inlet.objects.filter(pk=self.kwargs.get("pk")).select_subclasses().first()
        )

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
