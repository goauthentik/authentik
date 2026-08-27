import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, SCIMMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-provider-scim-form")
export class PropertyMappingProviderSCIMForm extends BasePropertyMappingForm<SCIMMapping> {
    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsProviderScimRetrieve({ pmUuid: pk }),
        create: (sCIMMappingRequest: SCIMMapping) =>
            aki(PropertymappingsApi).propertymappingsProviderScimCreate({ sCIMMappingRequest }),
        update: (pk: string, sCIMMappingRequest: SCIMMapping) =>
            aki(PropertymappingsApi).propertymappingsProviderScimUpdate({
                pmUuid: pk,
                sCIMMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-scim-form": PropertyMappingProviderSCIMForm;
    }
}
