import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, SCIMSourcePropertyMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-scim-form")
export class PropertyMappingSourceSCIMForm extends BasePropertyMappingForm<SCIMSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsSourceScimRetrieve({ pmUuid: pk }),
        create: (sCIMSourcePropertyMappingRequest: SCIMSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceScimCreate({
                sCIMSourcePropertyMappingRequest,
            }),
        update: (pk: string, sCIMSourcePropertyMappingRequest: SCIMSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceScimUpdate({
                pmUuid: pk,
                sCIMSourcePropertyMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-scim-form": PropertyMappingSourceSCIMForm;
    }
}
