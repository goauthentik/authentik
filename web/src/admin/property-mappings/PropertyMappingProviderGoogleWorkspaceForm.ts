import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { GoogleWorkspaceProviderMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-provider-google-workspace-form")
export class PropertyMappingProviderGoogleWorkspaceForm extends BasePropertyMappingForm<GoogleWorkspaceProviderMapping> {
    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsProviderGoogleWorkspaceRetrieve({
                pmUuid: pk,
            }),
        create: (googleWorkspaceProviderMappingRequest: GoogleWorkspaceProviderMapping) =>
            aki(PropertymappingsApi).propertymappingsProviderGoogleWorkspaceCreate({
                googleWorkspaceProviderMappingRequest,
            }),
        update: (
            pk: string,
            googleWorkspaceProviderMappingRequest: GoogleWorkspaceProviderMapping,
        ) =>
            aki(PropertymappingsApi).propertymappingsProviderGoogleWorkspaceUpdate({
                pmUuid: pk,
                googleWorkspaceProviderMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-google-workspace-form": PropertyMappingProviderGoogleWorkspaceForm;
    }
}
