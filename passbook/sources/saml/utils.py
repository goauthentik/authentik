"""saml sp helpers"""
from django.http import HttpRequest
from django.shortcuts import reverse

from passbook.core.models import User
from passbook.sources.saml.models import SAMLSource


def get_entity_id(request: HttpRequest, source: SAMLSource):
    """Get Source's entity ID, falling back to our Metadata URL if none is set"""
    entity_id = source.entity_id
    if entity_id is None:
        return build_full_url("metadata", request, source)
    return entity_id


def build_full_url(view: str, request: HttpRequest, source: SAMLSource) -> str:
    """Build Full ACS URL to be used in IDP"""
    return request.build_absolute_uri(
        reverse(f"passbook_sources_saml:{view}", kwargs={"source": source.slug})
    )


def _get_email_from_response(root):
    """
    Returns the email out of the response.

    At present, response must pass the email address as the Subject, eg.:

    <saml:Subject>
            <saml:NameID Format="urn:oasis:names:tc:SAML:2.0:nameid-format:email"
                         SPNameQualifier=""
                         >email@example.com</saml:NameID>
    """
    assertion = root.find("{urn:oasis:names:tc:SAML:2.0:assertion}Assertion")
    subject = assertion.find("{urn:oasis:names:tc:SAML:2.0:assertion}Subject")
    name_id = subject.find("{urn:oasis:names:tc:SAML:2.0:assertion}NameID")
    return name_id.text


def _get_attributes_from_response(root):
    """
    Returns the SAML Attributes (if any) that are present in the response.

    NOTE: Technically, attribute values could be any XML structure.
          But for now, just assume a single string value.
    """
    flat_attributes = {}
    assertion = root.find("{urn:oasis:names:tc:SAML:2.0:assertion}Assertion")
    attributes = assertion.find(
        "{urn:oasis:names:tc:SAML:2.0:assertion}AttributeStatement"
    )
    for attribute in attributes.getchildren():
        name = attribute.attrib.get("Name")
        children = attribute.getchildren()
        if not children:
            # Ignore empty-valued attributes. (I think these are not allowed.)
            continue
        if len(children) == 1:
            # See NOTE:
            flat_attributes[name] = children[0].text
        else:
            # It has multiple values.
            for child in children:
                # See NOTE:
                flat_attributes.setdefault(name, []).append(child.text)
    return flat_attributes


def _get_user_from_response(root):
    """
    Gets info out of the response and locally logs in this user.
    May create a local user account first.
    Returns the user object that was created.
    """
    email = _get_email_from_response(root)
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        user = User.objects.create_user(username=email, email=email)
        user.set_unusable_password()
        user.save()
    return user
