"""passbook Outlet administration"""
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

from passbook.core.models import Outlet
from passbook.lib.utils.reflection import all_subclasses, path_to_class
from passbook.lib.views import CreateAssignPermView


class OutletListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all outlets"""

    model = Outlet
    permission_required = "passbook_core.add_outlet"
    template_name = "administration/outlet/list.html"
    paginate_by = 10
    ordering = "id"

    def get_context_data(self, **kwargs):
        kwargs["types"] = {
            x.__name__: x._meta.verbose_name for x in all_subclasses(Outlet)
        }
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class OutletCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Outlet"""

    model = Outlet
    permission_required = "passbook_core.add_outlet"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:outlets")
    success_message = _("Successfully created Outlet")

    def get_form_class(self):
        outlet_type = self.request.GET.get("type")
        model = next(x for x in all_subclasses(Outlet) if x.__name__ == outlet_type)
        if not model:
            raise Http404
        return path_to_class(model.form)


class OutletUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update outlet"""

    model = Outlet
    permission_required = "passbook_core.change_outlet"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:outlets")
    success_message = _("Successfully updated Outlet")

    def get_form_class(self):
        form_class_path = self.get_object().form
        form_class = path_to_class(form_class_path)
        return form_class

    def get_object(self, queryset=None):
        return (
            Outlet.objects.filter(pk=self.kwargs.get("pk")).select_subclasses().first()
        )


class OutletDeleteView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete outlet"""

    model = Outlet
    permission_required = "passbook_core.delete_outlet"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:outlets")
    success_message = _("Successfully deleted Outlet")

    def get_object(self, queryset=None):
        return (
            Outlet.objects.filter(pk=self.kwargs.get("pk")).select_subclasses().first()
        )

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
