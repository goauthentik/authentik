import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, RadiusProviderPropertyMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-provider-radius-form")
export class PropertyMappingProviderRadiusForm extends BasePropertyMappingForm<RadiusProviderPropertyMapping> {
    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsProviderRadiusRetrieve({ pmUuid: pk }),
        create: (radiusProviderPropertyMappingRequest: RadiusProviderPropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsProviderRadiusCreate({
                radiusProviderPropertyMappingRequest,
            }),
        update: (pk: string, radiusProviderPropertyMappingRequest: RadiusProviderPropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsProviderRadiusUpdate({
                pmUuid: pk,
                radiusProviderPropertyMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-radius-form": PropertyMappingProviderRadiusForm;
    }
}
