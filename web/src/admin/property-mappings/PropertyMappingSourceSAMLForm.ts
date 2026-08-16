import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, SAMLSourcePropertyMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-saml-form")
export class PropertyMappingSourceSAMLForm extends BasePropertyMappingForm<SAMLSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsSourceSamlRetrieve({ pmUuid: pk }),
        create: (sAMLSourcePropertyMappingRequest: SAMLSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceSamlCreate({
                sAMLSourcePropertyMappingRequest,
            }),
        update: (pk: string, sAMLSourcePropertyMappingRequest: SAMLSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceSamlUpdate({
                pmUuid: pk,
                sAMLSourcePropertyMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-saml-form": PropertyMappingSourceSAMLForm;
    }
}
