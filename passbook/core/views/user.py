"""passbook core user views"""
from typing import Any, Dict

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import UpdateView

from passbook.core.forms.users import UserDetailForm
from passbook.flows.models import Flow, FlowDesignation


class UserSettingsView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    """Update User settings"""

    template_name = "user/settings.html"
    form_class = UserDetailForm

    success_message = _("Successfully updated user.")
    success_url = reverse_lazy("passbook_core:user-settings")

    def get_object(self):
        return self.request.user

    def get_context_data(self, **kwargs: Any) -> Dict[str, Any]:
        kwargs = super().get_context_data(**kwargs)
        unenrollment_flow = Flow.with_policy(
            self.request, designation=FlowDesignation.UNRENOLLMENT
        )
        kwargs["unenrollment_enabled"] = bool(unenrollment_flow)
        return kwargs
