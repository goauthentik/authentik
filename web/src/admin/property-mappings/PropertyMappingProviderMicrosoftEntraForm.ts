import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { MicrosoftEntraProviderMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-provider-microsoft-entra-form")
export class PropertyMappingProviderMicrosoftEntraForm extends BasePropertyMappingForm<MicrosoftEntraProviderMapping> {
    loadInstance(pk: string): Promise<MicrosoftEntraProviderMapping> {
        return aki(PropertymappingsApi).propertymappingsProviderMicrosoftEntraRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: MicrosoftEntraProviderMapping): Promise<MicrosoftEntraProviderMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsProviderMicrosoftEntraUpdate({
                pmUuid: this.instance.pk,
                microsoftEntraProviderMappingRequest: data,
            });
        }

        return aki(PropertymappingsApi).propertymappingsProviderMicrosoftEntraCreate({
            microsoftEntraProviderMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-microsoft-entra-form": PropertyMappingProviderMicrosoftEntraForm;
    }
}
