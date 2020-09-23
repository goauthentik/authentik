"""passbook Proxy Provider Forms"""
from django import forms

from passbook.crypto.models import CertificateKeyPair
from passbook.flows.models import Flow, FlowDesignation
from passbook.providers.proxy.models import ProxyProvider


class ProxyProviderForm(forms.ModelForm):
    """Security Gateway Provider form"""

    instance: ProxyProvider

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["authorization_flow"].queryset = Flow.objects.filter(
            designation=FlowDesignation.AUTHORIZATION
        )
        self.fields["certificate"].queryset = CertificateKeyPair.objects.filter(
            key_data__isnull=False
        )

    def save(self, *args, **kwargs):
        actual_save = super().save(*args, **kwargs)
        self.instance.set_oauth_defaults()
        self.instance.save()
        return actual_save

    class Meta:

        model = ProxyProvider
        fields = [
            "name",
            "authorization_flow",
            "internal_host",
            "internal_host_ssl_validation",
            "external_host",
            "certificate",
            "skip_path_regex",
        ]
        widgets = {
            "name": forms.TextInput(),
            "internal_host": forms.TextInput(),
            "external_host": forms.TextInput(),
        }
