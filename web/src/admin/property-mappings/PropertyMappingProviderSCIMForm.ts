import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { PropertymappingsApi, SCIMMapping } from "@goauthentik/api";

@customElement("ak-property-mapping-provider-scim-form")
export class PropertyMappingProviderSCIMForm extends BasePropertyMappingForm<SCIMMapping> {
    loadInstance(pk: string): Promise<SCIMMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsProviderScimRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: SCIMMapping): Promise<SCIMMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsProviderScimUpdate({
                pmUuid: this.instance.pk,
                sCIMMappingRequest: data,
            });
        }
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsProviderScimCreate({
            sCIMMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-scim-form": PropertyMappingProviderSCIMForm;
    }
}
