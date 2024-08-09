import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { PropertymappingsApi, SCIMMapping } from "@goauthentik/api";

@customElement("ak-property-mapping-scim-form")
export class PropertyMappingSCIMForm extends BasePropertyMappingForm<SCIMMapping> {
    loadInstance(pk: string): Promise<SCIMMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsScimRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: SCIMMapping): Promise<SCIMMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsScimUpdate({
                pmUuid: this.instance.pk,
                sCIMMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsScimCreate({
                sCIMMappingRequest: data,
            });
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-scim-form": PropertyMappingSCIMForm;
    }
}
