import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { PropertymappingsApi, RadiusProviderPropertyMapping } from "@goauthentik/api";

@customElement("ak-property-mapping-radius-form")
export class PropertyMappingRadiusForm extends BasePropertyMappingForm<RadiusProviderPropertyMapping> {
    loadInstance(pk: string): Promise<RadiusProviderPropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsRadiusRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: RadiusProviderPropertyMapping): Promise<RadiusProviderPropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsRadiusUpdate({
                pmUuid: this.instance.pk,
                radiusProviderPropertyMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsRadiusCreate({
                radiusProviderPropertyMappingRequest: data,
            });
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-radius-form": PropertyMappingRadiusForm;
    }
}
