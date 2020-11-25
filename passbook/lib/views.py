"""passbook helper views"""
from django.http import HttpRequest
from django.template.response import TemplateResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import CreateView
from guardian.shortcuts import assign_perm


class CreateAssignPermView(CreateView):
    """Assign permissions to object after creation"""

    permissions = [
        "%s.view_%s",
        "%s.change_%s",
        "%s.delete_%s",
    ]

    def form_valid(self, form):
        response = super().form_valid(form)
        for permission in self.permissions:
            full_permission = permission % (
                self.object._meta.app_label,
                self.object._meta.model_name,
            )
            assign_perm(full_permission, self.request.user, self.object)
        return response


def bad_request_message(
    request: HttpRequest,
    message: str,
    title="Bad Request",
    template="error/generic.html",
) -> TemplateResponse:
    """Return generic error page with message, with status code set to 400"""
    return TemplateResponse(
        request,
        template,
        {"message": message, "title": _(title)},
        status=400,
    )
