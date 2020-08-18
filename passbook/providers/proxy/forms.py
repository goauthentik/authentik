"""passbook Proxy Provider Forms"""
from django import forms

from passbook.providers.proxy.models import ProxyProvider


class ProxyProviderForm(forms.ModelForm):
    """Security Gateway Provider form"""

    instance: ProxyProvider

    def save(self, *args, **kwargs):
        self.instance.set_oauth_defaults()
        return super().save(*args, **kwargs)

    class Meta:

        model = ProxyProvider
        fields = ["name", "authorization_flow", "internal_host", "external_host"]
        widgets = {
            "name": forms.TextInput(),
            "internal_host": forms.TextInput(),
            "external_host": forms.TextInput(),
        }
