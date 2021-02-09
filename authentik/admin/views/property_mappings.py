"""authentik PropertyMapping administration"""
from json import dumps
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import FormView
from django.views.generic.detail import DetailView
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.forms.policies import PolicyTestForm
from authentik.admin.views.utils import (
    BackSuccessUrlMixin,
    DeleteMessageView,
    InheritanceCreateView,
    InheritanceUpdateView,
)
from authentik.core.models import PropertyMapping


class PropertyMappingCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    InheritanceCreateView,
):
    """Create new PropertyMapping"""

    model = PropertyMapping
    permission_required = "authentik_core.add_propertymapping"

    template_name = "generic/create.html"
    success_message = _("Successfully created Property Mapping")


class PropertyMappingUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    InheritanceUpdateView,
):
    """Update property_mapping"""

    model = PropertyMapping
    permission_required = "authentik_core.change_propertymapping"

    template_name = "generic/update.html"
    success_message = _("Successfully updated Property Mapping")


class PropertyMappingDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete property_mapping"""

    model = PropertyMapping
    permission_required = "authentik_core.delete_propertymapping"

    template_name = "generic/delete.html"
    success_message = _("Successfully deleted Property Mapping")


class PropertyMappingTestView(
    LoginRequiredMixin, DetailView, PermissionRequiredMixin, FormView
):
    """View to test property mappings"""

    model = PropertyMapping
    form_class = PolicyTestForm
    permission_required = "authentik_core.view_propertymapping"
    template_name = "administration/property_mapping/test.html"
    object = None

    def get_object(self, queryset=None) -> PropertyMapping:
        return (
            PropertyMapping.objects.filter(pk=self.kwargs.get("pk"))
            .select_subclasses()
            .first()
        )

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        kwargs["property_mapping"] = self.get_object()
        return super().get_context_data(**kwargs)

    def post(self, *args, **kwargs) -> HttpResponse:
        self.object = self.get_object()
        return super().post(*args, **kwargs)

    def form_valid(self, form: PolicyTestForm) -> HttpResponse:
        mapping = self.get_object()
        user = form.cleaned_data.get("user")

        context = self.get_context_data(form=form)
        try:
            result = mapping.evaluate(
                user, self.request, **form.cleaned_data.get("context", {})
            )
            context["result"] = dumps(result, indent=4)
        except Exception as exc:  # pylint: disable=broad-except
            context["result"] = str(exc)
        return self.render_to_response(context)
