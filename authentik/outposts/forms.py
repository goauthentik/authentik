"""Outpost forms"""

from django import forms
from django.utils.translation import gettext_lazy as _

from authentik.admin.fields import CodeMirrorWidget, YAMLField
from authentik.crypto.models import CertificateKeyPair
from authentik.outposts.models import (
    DockerServiceConnection,
    KubernetesServiceConnection,
    Outpost,
    OutpostServiceConnection,
)
from authentik.providers.proxy.models import ProxyProvider


class OutpostForm(forms.ModelForm):
    """Outpost Form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["providers"].queryset = ProxyProvider.objects.all()
        self.fields[
            "service_connection"
        ].queryset = OutpostServiceConnection.objects.select_subclasses()

    class Meta:

        model = Outpost
        fields = [
            "name",
            "type",
            "service_connection",
            "providers",
            "_config",
        ]
        widgets = {
            "name": forms.TextInput(),
            "_config": CodeMirrorWidget,
        }
        field_classes = {
            "_config": YAMLField,
        }
        labels = {"_config": _("Configuration")}


class DockerServiceConnectionForm(forms.ModelForm):
    """Docker service-connection form"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["tls_authentication"].queryset = CertificateKeyPair.objects.filter(
            key_data__isnull=False
        )

    class Meta:

        model = DockerServiceConnection
        fields = ["name", "local", "url", "tls_verification", "tls_authentication"]
        widgets = {
            "name": forms.TextInput,
            "url": forms.TextInput,
        }
        labels = {
            "url": _("URL"),
            "tls_verification": _("TLS Verification Certificate"),
            "tls_authentication": _("TLS Authentication Certificate"),
        }


class KubernetesServiceConnectionForm(forms.ModelForm):
    """Kubernetes service-connection form"""

    class Meta:

        model = KubernetesServiceConnection
        fields = [
            "name",
            "local",
            "kubeconfig",
        ]
        widgets = {
            "name": forms.TextInput,
            "kubeconfig": CodeMirrorWidget,
        }
        field_classes = {
            "kubeconfig": YAMLField,
        }
