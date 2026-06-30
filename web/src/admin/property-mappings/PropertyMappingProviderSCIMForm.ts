import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, SCIMMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-provider-scim-form")
export class PropertyMappingProviderSCIMForm extends BasePropertyMappingForm<SCIMMapping> {
    loadInstance(pk: string): Promise<SCIMMapping> {
        return aki(PropertymappingsApi).propertymappingsProviderScimRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: SCIMMapping): Promise<SCIMMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsProviderScimUpdate({
                pmUuid: this.instance.pk,
                sCIMMappingRequest: data,
            });
        }

        return aki(PropertymappingsApi).propertymappingsProviderScimCreate({
            sCIMMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-scim-form": PropertyMappingProviderSCIMForm;
    }
}
