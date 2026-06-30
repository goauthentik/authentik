import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, SCIMSourcePropertyMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-scim-form")
export class PropertyMappingSourceSCIMForm extends BasePropertyMappingForm<SCIMSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    loadInstance(pk: string): Promise<SCIMSourcePropertyMapping> {
        return aki(PropertymappingsApi).propertymappingsSourceScimRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: SCIMSourcePropertyMapping): Promise<SCIMSourcePropertyMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsSourceScimUpdate({
                pmUuid: this.instance.pk,
                sCIMSourcePropertyMappingRequest: data,
            });
        }

        return aki(PropertymappingsApi).propertymappingsSourceScimCreate({
            sCIMSourcePropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-scim-form": PropertyMappingSourceSCIMForm;
    }
}
