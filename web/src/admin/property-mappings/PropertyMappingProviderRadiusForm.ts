import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { PropertymappingsApi, RadiusProviderPropertyMapping } from "@goauthentik/api";

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
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsProviderRadiusCreate({
                radiusProviderPropertyMappingRequest: data,
            });
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-radius-form": PropertyMappingProviderRadiusForm;
    }
}
