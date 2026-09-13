import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { MicrosoftEntraProviderMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-provider-microsoft-entra-form")
export class PropertyMappingProviderMicrosoftEntraForm extends BasePropertyMappingForm<MicrosoftEntraProviderMapping> {
    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsProviderMicrosoftEntraRetrieve({
                pmUuid: pk,
            }),
        create: (microsoftEntraProviderMappingRequest: MicrosoftEntraProviderMapping) =>
            aki(PropertymappingsApi).propertymappingsProviderMicrosoftEntraCreate({
                microsoftEntraProviderMappingRequest,
            }),
        update: (pk: string, microsoftEntraProviderMappingRequest: MicrosoftEntraProviderMapping) =>
            aki(PropertymappingsApi).propertymappingsProviderMicrosoftEntraUpdate({
                pmUuid: pk,
                microsoftEntraProviderMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-microsoft-entra-form": PropertyMappingProviderMicrosoftEntraForm;
    }
}
