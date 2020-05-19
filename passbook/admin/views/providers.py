"""passbook Provider administration"""
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

from passbook.core.models import Provider
from passbook.lib.utils.reflection import all_subclasses, path_to_class
from passbook.lib.views import CreateAssignPermView


class ProviderListView(LoginRequiredMixin, PermissionListMixin, ListView):
    """Show list of all providers"""

    model = Provider
    permission_required = "passbook_core.add_provider"
    template_name = "administration/provider/list.html"
    paginate_by = 10
    ordering = "id"

    def get_context_data(self, **kwargs):
        kwargs["types"] = {
            x.__name__: x._meta.verbose_name for x in all_subclasses(Provider)
        }
        return super().get_context_data(**kwargs)

    def get_queryset(self):
        return super().get_queryset().select_subclasses()


class ProviderCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new Provider"""

    model = Provider
    permission_required = "passbook_core.add_provider"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:providers")
    success_message = _("Successfully created Provider")

    def get_form_class(self):
        provider_type = self.request.GET.get("type")
        try:
            model = next(
                x for x in all_subclasses(Provider) if x.__name__ == provider_type
            )
        except StopIteration as exc:
            raise Http404 from exc
        return path_to_class(model.form)


class ProviderUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update provider"""

    model = Provider
    permission_required = "passbook_core.change_provider"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:providers")
    success_message = _("Successfully updated Provider")

    def get_form_class(self):
        form_class_path = self.get_object().form
        form_class = path_to_class(form_class_path)
        return form_class

    def get_object(self, queryset=None):
        return (
            Provider.objects.filter(pk=self.kwargs.get("pk"))
            .select_subclasses()
            .first()
        )


class ProviderDeleteView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, DeleteView
):
    """Delete provider"""

    model = Provider
    permission_required = "passbook_core.delete_provider"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:providers")
    success_message = _("Successfully deleted Provider")

    def get_object(self, queryset=None):
        return (
            Provider.objects.filter(pk=self.kwargs.get("pk"))
            .select_subclasses()
            .first()
        )

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)
