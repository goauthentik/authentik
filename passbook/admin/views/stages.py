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
from passbook.lib.utils.reflection import all_subclasses, path_to_class
from passbook.lib.views import CreateAssignPermView


class StageListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all stages"""

    model = Stage
    template_name = "administration/stage/list.html"
    permission_required = "passbook_flows.view_stage"
    ordering = "name"
    paginate_by = 40

    def get_context_data(self, **kwargs):
        kwargs["types"] = {x.__name__: x for x in all_subclasses(Stage)}
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
    permission_required = "passbook_flows.add_stage"

    success_url = reverse_lazy("passbook_admin:stages")
    success_message = _("Successfully created Stage")

    def get_context_data(self, **kwargs):
        kwargs = super().get_context_data(**kwargs)
        stage_type = self.request.GET.get("type")
        model = next(x for x in all_subclasses(Stage) if x.__name__ == stage_type)
        kwargs["type"] = model._meta.verbose_name
        return kwargs

    def get_form_class(self):
        stage_type = self.request.GET.get("type")
        try:
            model = next(x for x in all_subclasses(Stage) if x.__name__ == stage_type)
        except StopIteration as exc:
            raise Http404 from exc
        return path_to_class(model.form)


class StageUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update stage"""

    model = Stage
    permission_required = "passbook_flows.update_application"
    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:stages")
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
    """Delete stage"""

    model = Stage
    template_name = "generic/delete.html"
    permission_required = "passbook_flows.delete_stage"
    success_url = reverse_lazy("passbook_admin:stages")
    success_message = _("Successfully deleted Stage")

    def get_object(self, queryset=None):
        return (
            Stage.objects.filter(pk=self.kwargs.get("pk")).select_subclasses().first()
        )

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
