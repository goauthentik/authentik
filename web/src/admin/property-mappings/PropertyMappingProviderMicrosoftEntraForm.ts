import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { MicrosoftEntraProviderMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-provider-microsoft-entra-form")
export class PropertyMappingProviderMicrosoftEntraForm extends BasePropertyMappingForm<MicrosoftEntraProviderMapping> {
    loadInstance(pk: string): Promise<MicrosoftEntraProviderMapping> {
        return new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsProviderMicrosoftEntraRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: MicrosoftEntraProviderMapping): Promise<MicrosoftEntraProviderMapping> {
        if (this.instance) {
            return new PropertymappingsApi(
                DEFAULT_CONFIG,
            ).propertymappingsProviderMicrosoftEntraUpdate({
                pmUuid: this.instance.pk,
                microsoftEntraProviderMappingRequest: data,
            });
        }
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsProviderMicrosoftEntraCreate(
            {
                microsoftEntraProviderMappingRequest: data,
            },
        );
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-microsoft-entra-form": PropertyMappingProviderMicrosoftEntraForm;
    }
}
