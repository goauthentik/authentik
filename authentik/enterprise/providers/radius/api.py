from django.utils.translation import gettext as _
from rest_framework.exceptions import ValidationError

from authentik.crypto.models import CertificateKeyPair
from authentik.enterprise.license import LicenseKey


class RadiusProviderSerializerMixin:

    def validate_certificate(self, cert: CertificateKeyPair) -> CertificateKeyPair:
        if cert:
            if not LicenseKey.cached_summary().status.is_valid:
                raise ValidationError(_("Enterprise is required to use EAP-TLS."))
        return cert
