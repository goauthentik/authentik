"""SAML Provider managed objects"""
from authentik.managed.manager import EnsureExists, ObjectManager
from authentik.providers.saml.models import SAMLPropertyMapping


class SAMLProviderManager(ObjectManager):
    """SAML Provider managed objects"""

    def reconcile(self):
        return [
            EnsureExists(
                SAMLPropertyMapping,
                "saml_name",
                name="authentik default SAML Mapping: UPN",
                saml_name="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/upn",
                expression="return user.attributes.get('upn', user.email)",
            ),
            EnsureExists(
                SAMLPropertyMapping,
                "saml_name",
                name="authentik default SAML Mapping: Name",
                saml_name="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/name",
                expression="return user.name",
            ),
            EnsureExists(
                SAMLPropertyMapping,
                "saml_name",
                name="authentik default SAML Mapping: Email",
                saml_name="http://schemas.xmlsoap.org/ws/2005/05/identity/claims/emailaddress",
                expression="return user.email",
            ),
            EnsureExists(
                SAMLPropertyMapping,
                "saml_name",
                name="authentik default SAML Mapping: Username",
                saml_name="http://schemas.goauthentik.io/2021/02/saml/username",
                expression="return user.username",
            ),
            EnsureExists(
                SAMLPropertyMapping,
                "saml_name",
                name="authentik default SAML Mapping: User ID",
                saml_name="http://schemas.goauthentik.io/2021/02/saml/uid",
                expression="return user.pk",
            ),
            EnsureExists(
                SAMLPropertyMapping,
                "saml_name",
                name="authentik default SAML Mapping: WindowsAccountname (Username)",
                saml_name=(
                    "http://schemas.microsoft.com/ws/2008/06/identity/claims/windowsaccountname"
                ),
                expression="return user.username",
            ),
            EnsureExists(
                SAMLPropertyMapping,
                "saml_name",
                name="authentik default SAML Mapping: Groups",
                saml_name="http://schemas.xmlsoap.org/claims/Group",
                expression="for group in user.ak_groups.all():\n    yield group.name",
            ),
        ]
