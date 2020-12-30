"""authentik Proxy Provider Forms"""
from django import forms

from authentik.crypto.models import CertificateKeyPair
from authentik.flows.models import Flow, FlowDesignation
from authentik.providers.proxy.models import ProxyProvider


class ProxyProviderForm(forms.ModelForm):
    """Proxy Provider form"""

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
            "basic_auth_enabled",
            "basic_auth_user_attribute",
            "basic_auth_password_attribute",
        ]
        widgets = {
            "name": forms.TextInput(),
            "internal_host": forms.TextInput(),
            "external_host": forms.TextInput(),
            "basic_auth_user_attribute": forms.TextInput(),
            "basic_auth_password_attribute": forms.TextInput(),
        }
