import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";

import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { GoogleWorkspaceProviderMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

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
        }
        return new PropertymappingsApi(
            DEFAULT_CONFIG,
        ).propertymappingsProviderGoogleWorkspaceCreate({
            googleWorkspaceProviderMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-google-workspace-form": PropertyMappingProviderGoogleWorkspaceForm;
    }
}
