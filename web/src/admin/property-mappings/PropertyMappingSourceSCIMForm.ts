import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { PropertymappingsApi, SCIMSourcePropertyMapping } from "@goauthentik/api";

@customElement("ak-property-mapping-source-scim-form")
export class PropertyMappingSourceSCIMForm extends BasePropertyMappingForm<SCIMSourcePropertyMapping> {
    docLink(): string {
        return "/docs/users-sources/sources/property-mappings/expressions?utm_source=authentik";
    }

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
