"""authentik CertificateKeyPair administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http.response import HttpResponse
from django.utils.translation import gettext as _
from django.views.generic import UpdateView
from django.views.generic.edit import FormView
from guardian.mixins import PermissionRequiredMixin

from authentik.admin.views.utils import BackSuccessUrlMixin, DeleteMessageView
from authentik.crypto.builder import CertificateBuilder
from authentik.crypto.forms import (
    CertificateKeyPairForm,
    CertificateKeyPairGenerateForm,
)
from authentik.crypto.models import CertificateKeyPair
from authentik.lib.views import CreateAssignPermView


class CertificateKeyPairCreateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new CertificateKeyPair"""

    model = CertificateKeyPair
    form_class = CertificateKeyPairForm
    permission_required = "authentik_crypto.add_certificatekeypair"

    template_name = "generic/create.html"
    success_url = "/"
    success_message = _("Successfully created Certificate-Key Pair")


class CertificateKeyPairGenerateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    FormView,
):
    """Generate new CertificateKeyPair"""

    model = CertificateKeyPair
    form_class = CertificateKeyPairGenerateForm
    permission_required = "authentik_crypto.add_certificatekeypair"

    template_name = "administration/certificatekeypair/generate.html"
    success_url = "/"
    success_message = _("Successfully generated Certificate-Key Pair")

    def form_valid(self, form: CertificateKeyPairGenerateForm) -> HttpResponse:
        builder = CertificateBuilder()
        builder.common_name = form.data["common_name"]
        builder.build(
            subject_alt_names=form.data.get("subject_alt_name", "").split(","),
            validity_days=int(form.data["validity_days"]),
        )
        builder.save()
        return super().form_valid(form)


class CertificateKeyPairUpdateView(
    SuccessMessageMixin,
    BackSuccessUrlMixin,
    LoginRequiredMixin,
    PermissionRequiredMixin,
    UpdateView,
):
    """Update certificatekeypair"""

    model = CertificateKeyPair
    form_class = CertificateKeyPairForm
    permission_required = "authentik_crypto.change_certificatekeypair"

    template_name = "generic/update.html"
    success_url = "/"
    success_message = _("Successfully updated Certificate-Key Pair")


class CertificateKeyPairDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete certificatekeypair"""

    model = CertificateKeyPair
    permission_required = "authentik_crypto.delete_certificatekeypair"

    template_name = "generic/delete.html"
    success_url = "/"
    success_message = _("Successfully deleted Certificate-Key Pair")
