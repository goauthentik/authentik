import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, RadiusProviderPropertyMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-provider-radius-form")
export class PropertyMappingProviderRadiusForm extends BasePropertyMappingForm<RadiusProviderPropertyMapping> {
    loadInstance(pk: string): Promise<RadiusProviderPropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsProviderRadiusRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: RadiusProviderPropertyMapping): Promise<RadiusProviderPropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsProviderRadiusUpdate({
                pmUuid: this.instance.pk,
                radiusProviderPropertyMappingRequest: data,
            });
        }
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsProviderRadiusCreate({
            radiusProviderPropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-radius-form": PropertyMappingProviderRadiusForm;
    }
}
