"""passbook Source administration"""
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

from passbook.core.models import Source
from passbook.lib.utils.reflection import all_subclasses, path_to_class
from passbook.lib.views import CreateAssignPermView


class SourceListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all sources"""

    model = Source
    permission_required = "passbook_core.view_source"
    ordering = "name"
    paginate_by = 40
    template_name = "administration/source/list.html"

    def get_context_data(self, **kwargs):
        kwargs["types"] = {
            x.__name__: x for x in all_subclasses(Source)
        }
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class SourceCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Source"""

    model = Source
    permission_required = "passbook_core.add_source"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:sources")
    success_message = _("Successfully created Source")

    def get_form_class(self):
        source_type = self.request.GET.get("type")
        try:
            model = next(x for x in all_subclasses(Source) if x.__name__ == source_type)
        except StopIteration as exc:
            raise Http404 from exc
        return path_to_class(model.form)


class SourceUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update source"""

    model = Source
    permission_required = "passbook_core.change_source"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:sources")
    success_message = _("Successfully updated Source")

    def get_form_class(self):
        form_class_path = self.get_object().form
        form_class = path_to_class(form_class_path)
        return form_class

    def get_object(self, queryset=None):
        return (
            Source.objects.filter(pk=self.kwargs.get("pk")).select_subclasses().first()
        )


class SourceDeleteView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete source"""

    model = Source
    permission_required = "passbook_core.delete_source"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:sources")
    success_message = _("Successfully deleted Source")

    def get_object(self, queryset=None):
        return (
            Source.objects.filter(pk=self.kwargs.get("pk")).select_subclasses().first()
        )

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
