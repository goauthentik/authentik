"""passbook CertificateKeyPair administration"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import (
    PermissionRequiredMixin as DjangoPermissionRequiredMixin,
)
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext as _
from django.views.generic import ListView, UpdateView
from guardian.mixins import PermissionListMixin, PermissionRequiredMixin

from passbook.admin.views.utils import DeleteMessageView, UserPaginateListMixin
from passbook.crypto.forms import CertificateKeyPairForm
from passbook.crypto.models import CertificateKeyPair
from passbook.lib.views import CreateAssignPermView


class CertificateKeyPairListView(LoginRequiredMixin, PermissionListMixin, UserPaginateListMixin, ListView):
    """Show list of all keypairs"""

    model = CertificateKeyPair
    permission_required = "passbook_crypto.view_certificatekeypair"
    ordering = "name"
    template_name = "administration/certificatekeypair/list.html"


class CertificateKeyPairCreateView(
    SuccessMessageMixin,
    LoginRequiredMixin,
    DjangoPermissionRequiredMixin,
    CreateAssignPermView,
):
    """Create new CertificateKeyPair"""

    model = CertificateKeyPair
    form_class = CertificateKeyPairForm
    permission_required = "passbook_crypto.add_certificatekeypair"

    template_name = "generic/create.html"
    success_url = reverse_lazy("passbook_admin:certificate_key_pair")
    success_message = _("Successfully created CertificateKeyPair")


class CertificateKeyPairUpdateView(
    SuccessMessageMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView
):
    """Update certificatekeypair"""

    model = CertificateKeyPair
    form_class = CertificateKeyPairForm
    permission_required = "passbook_crypto.change_certificatekeypair"

    template_name = "generic/update.html"
    success_url = reverse_lazy("passbook_admin:certificate_key_pair")
    success_message = _("Successfully updated Certificate-Key Pair")


class CertificateKeyPairDeleteView(
    LoginRequiredMixin, PermissionRequiredMixin, DeleteMessageView
):
    """Delete certificatekeypair"""

    model = CertificateKeyPair
    permission_required = "passbook_crypto.delete_certificatekeypair"

    template_name = "generic/delete.html"
    success_url = reverse_lazy("passbook_admin:certificate_key_pair")
    success_message = _("Successfully deleted Certificate-Key Pair")
