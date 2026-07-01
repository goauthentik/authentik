import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, RadiusProviderPropertyMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-provider-radius-form")
export class PropertyMappingProviderRadiusForm extends BasePropertyMappingForm<RadiusProviderPropertyMapping> {
    loadInstance(pk: string): Promise<RadiusProviderPropertyMapping> {
        return aki(PropertymappingsApi).propertymappingsProviderRadiusRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: RadiusProviderPropertyMapping): Promise<RadiusProviderPropertyMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsProviderRadiusUpdate({
                pmUuid: this.instance.pk,
                radiusProviderPropertyMappingRequest: data,
            });
        }

        return aki(PropertymappingsApi).propertymappingsProviderRadiusCreate({
            radiusProviderPropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-radius-form": PropertyMappingProviderRadiusForm;
    }
}
