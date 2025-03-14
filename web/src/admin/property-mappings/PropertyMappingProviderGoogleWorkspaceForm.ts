import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config.js";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { GoogleWorkspaceProviderMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-provider-google-workspace-form")
export class PropertyMappingProviderGoogleWorkspaceForm extends BasePropertyMappingForm<GoogleWorkspaceProviderMapping> {
    loadInstance(pk: string): Promise<GoogleWorkspaceProviderMapping> {
        return new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsProviderGoogleWorkspaceRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: GoogleWorkspaceProviderMapping): Promise<GoogleWorkspaceProviderMapping> {
        if (this.instance) {
            return new PropertymappingsApi(
                DEFAULT_CONFIG,
            ).propertymappingsProviderGoogleWorkspaceUpdate({
                pmUuid: this.instance.pk,
                googleWorkspaceProviderMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(
                DEFAULT_CONFIG,
            ).propertymappingsProviderGoogleWorkspaceCreate({
                googleWorkspaceProviderMappingRequest: data,
            });
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-google-workspace-form": PropertyMappingProviderGoogleWorkspaceForm;
    }
}
