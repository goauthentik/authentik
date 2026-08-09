import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PlexSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-plex-form")
export class PropertyMappingSourcePlexForm extends BasePropertyMappingForm<PlexSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsSourcePlexRetrieve({ pmUuid: pk }),
        create: (plexSourcePropertyMappingRequest: PlexSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourcePlexCreate({
                plexSourcePropertyMappingRequest,
            }),
        update: (pk: string, plexSourcePropertyMappingRequest: PlexSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourcePlexUpdate({
                pmUuid: pk,
                plexSourcePropertyMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-plex-form": PropertyMappingSourcePlexForm;
    }
}
