"""passbook Stage administration"""
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

from passbook.flows.models import Stage
from passbook.lib.utils.reflection import path_to_class
from passbook.lib.views import CreateAssignPermView


def all_subclasses(cls):
    """Recursively return all subclassess of cls"""
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)]
    )


class StageListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all flows"""

    model = Stage
    template_name = "administration/flow/list.html"
    permission_required = "passbook_core.view_flow"
    ordering = "order"
    paginate_by = 40

    def get_context_data(self, **kwargs):
        kwargs["types"] = {
            x.__name__: x._meta.verbose_name for x in all_subclasses(Stage)
        }
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class StageCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Stage"""

    model = Stage
    template_name = "generic/create.html"
    permission_required = "passbook_core.add_flow"

    success_url = reverse_lazy("passbook_admin:flows")
    success_message = _("Successfully created Stage")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        flow_type = self.request.GET.get("type")
        model = next(x for x in all_subclasses(Stage) if x.__name__ == flow_type)
        kwargs["type"] = model._meta.verbose_name
        return kwargs

    def get_form_class(self):
        flow_type = self.request.GET.get("type")
        model = next(x for x in all_subclasses(Stage) if x.__name__ == flow_type)
        if not model:
            raise Http404
        return path_to_class(model.form)


class StageUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update flow"""

    model = Stage
    permission_required = "passbook_core.update_application"
    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:flows")
    success_message = _("Successfully updated Stage")

    def get_form_class(self):
        form_class_path = self.get_object().form
        form_class = path_to_class(form_class_path)
        return form_class

    def get_object(self, queryset=None):
        return (
            Stage.objects.filter(pk=self.kwargs.get("pk")).select_subclasses().first()
        )


class StageDeleteView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete flow"""

    model = Stage
    template_name = "generic/delete.html"
    permission_required = "passbook_core.delete_flow"
    success_url = reverse_lazy("passbook_admin:flows")
    success_message = _("Successfully deleted Stage")

    def get_object(self, queryset=None):
        return (
            Stage.objects.filter(pk=self.kwargs.get("pk")).select_subclasses().first()
        )

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
