from django.urls import reverse
from lxml.etree import SubElement, _Element  # nosec

from authentik.common.saml.constants import NS_SAML_METADATA
from authentik.enterprise.providers.ws_federation.processors.constants import (
    NS_ADDRESSING,
    NS_MAP,
    NS_WS_FED_PROTOCOL,
    NS_WSI,
)
from authentik.providers.saml.processors.metadata import MetadataProcessor as BaseMetadataProcessor


class MetadataProcessor(BaseMetadataProcessor):
    def add_children(self, entity_descriptor: _Element):
        self.add_role_descriptor_sts(entity_descriptor)
        super().add_children(entity_descriptor)

    def add_endpoint(self, parent: _Element, name: str):
        endpoint = SubElement(parent, f"{{{NS_WS_FED_PROTOCOL}}}{name}", nsmap=NS_MAP)
        endpoint_ref = SubElement(endpoint, f"{{{NS_ADDRESSING}}}EndpointReference", nsmap=NS_MAP)

        address = SubElement(endpoint_ref, f"{{{NS_ADDRESSING}}}Address", nsmap=NS_MAP)
        address.text = self.http_request.build_absolute_uri(
            reverse("authentik_providers_ws_federation:wsfed")
        )

    def add_role_descriptor_sts(self, entity_descriptor: _Element):
        role_descriptor = SubElement(
            entity_descriptor, f"{{{NS_SAML_METADATA}}}RoleDescriptor", nsmap=NS_MAP
        )
        role_descriptor.attrib[f"{{{NS_WSI}}}type"] = "fed:SecurityTokenServiceType"
        role_descriptor.attrib["protocolSupportEnumeration"] = NS_WS_FED_PROTOCOL

        signing_descriptor = self.get_signing_key_descriptor()
        if signing_descriptor is not None:
            role_descriptor.append(signing_descriptor)

        self.add_endpoint(role_descriptor, "SecurityTokenServiceEndpoint")
        self.add_endpoint(role_descriptor, "PassiveRequestorEndpoint")
