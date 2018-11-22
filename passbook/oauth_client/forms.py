"""passbook oauth_client forms"""

from django import forms

from passbook.oauth_client.models import OAuthSource


class OAuthSourceForm(forms.ModelForm):
    """OAuthSource Form"""

    class Meta:

        model = OAuthSource
        # pylint: disable=modelform-uses-exclude
        exclude = []
