"""SAML Provider managed objects"""
from authentik.managed.manager import EnsureExists, ObjectManager
from authentik.providers.saml.models import SAMLPropertyMapping

GROUP_EXPRESSION = """
for group in user.ak_groups.all():
    yield group.name
"""


class SAMLProviderManager(ObjectManager):
    """SAML Provider managed objects"""

    def reconcile(self):
        return [
            EnsureExists(
                SAMLPropertyMapping,
                "goauthentik.io/providers/saml/upn",
                name="authentik default SAML Mapping: UPN",
                saml_name="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn",
                expression="return user.attributes.get('upn', user.email)",
                friendly_name="",
            ),
            EnsureExists(
                SAMLPropertyMapping,
                "goauthentik.io/providers/saml/name",
                name="authentik default SAML Mapping: Name",
                saml_name="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
                expression="return user.name",
                friendly_name="",
            ),
            EnsureExists(
                SAMLPropertyMapping,
                "goauthentik.io/providers/saml/email",
                name="authentik default SAML Mapping: Email",
                saml_name="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
                expression="return user.email",
                friendly_name="",
            ),
            EnsureExists(
                SAMLPropertyMapping,
                "goauthentik.io/providers/saml/username",
                name="authentik default SAML Mapping: Username",
                saml_name="http://schemas.goauthentik.io/2021/02/saml/username",
                expression="return user.username",
                friendly_name="",
            ),
            EnsureExists(
                SAMLPropertyMapping,
                "goauthentik.io/providers/saml/uid",
                name="authentik default SAML Mapping: User ID",
                saml_name="http://schemas.goauthentik.io/2021/02/saml/uid",
                expression="return user.pk",
                friendly_name="",
            ),
            EnsureExists(
                SAMLPropertyMapping,
                "goauthentik.io/providers/saml/groups",
                name="authentik default SAML Mapping: Groups",
                saml_name="http://schemas.xmlsoap.org/claims/Group",
                expression=GROUP_EXPRESSION,
                friendly_name="",
            ),
            EnsureExists(
                SAMLPropertyMapping,
                "goauthentik.io/providers/saml/ms-windowsaccountname",
                name="authentik default SAML Mapping: WindowsAccountname (Username)",
                saml_name=(
                    "http://schemas.microsoft.com/ws/2008/06/identity/claims/windowsaccountname"
                ),
                expression="return user.username",
                friendly_name="",
            ),
        ]
