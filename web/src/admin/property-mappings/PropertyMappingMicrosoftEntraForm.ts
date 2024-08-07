import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { MicrosoftEntraProviderMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-microsoft-entra-form")
export class PropertyMappingMicrosoftEntraForm extends BasePropertyMappingForm<MicrosoftEntraProviderMapping> {
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
        } else {
            return new PropertymappingsApi(
                DEFAULT_CONFIG,
            ).propertymappingsProviderMicrosoftEntraCreate({
                microsoftEntraProviderMappingRequest: data,
            });
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-microsoft-entra-form": PropertyMappingMicrosoftEntraForm;
    }
}
