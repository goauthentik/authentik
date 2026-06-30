import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { GoogleWorkspaceProviderMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-provider-google-workspace-form")
export class PropertyMappingProviderGoogleWorkspaceForm extends BasePropertyMappingForm<GoogleWorkspaceProviderMapping> {
    loadInstance(pk: string): Promise<GoogleWorkspaceProviderMapping> {
        return aki(PropertymappingsApi).propertymappingsProviderGoogleWorkspaceRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: GoogleWorkspaceProviderMapping): Promise<GoogleWorkspaceProviderMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsProviderGoogleWorkspaceUpdate({
                pmUuid: this.instance.pk,
                googleWorkspaceProviderMappingRequest: data,
            });
        }

        return aki(PropertymappingsApi).propertymappingsProviderGoogleWorkspaceCreate({
            googleWorkspaceProviderMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-google-workspace-form": PropertyMappingProviderGoogleWorkspaceForm;
    }
}
