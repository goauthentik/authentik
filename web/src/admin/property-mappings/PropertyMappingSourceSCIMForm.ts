import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, SCIMSourcePropertyMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-scim-form")
export class PropertyMappingSourceSCIMForm extends BasePropertyMappingForm<SCIMSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    loadInstance(pk: string): Promise<SCIMSourcePropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceScimRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: SCIMSourcePropertyMapping): Promise<SCIMSourcePropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceScimUpdate({
                pmUuid: this.instance.pk,
                sCIMSourcePropertyMappingRequest: data,
            });
        }
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceScimCreate({
            sCIMSourcePropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-scim-form": PropertyMappingSourceSCIMForm;
    }
}
