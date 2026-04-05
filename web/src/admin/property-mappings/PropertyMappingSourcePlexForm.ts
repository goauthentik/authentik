import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PlexSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-plex-form")
export class PropertyMappingSourcePlexForm extends BasePropertyMappingForm<PlexSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    loadInstance(pk: string): Promise<PlexSourcePropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourcePlexRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: PlexSourcePropertyMapping): Promise<PlexSourcePropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourcePlexUpdate({
                pmUuid: this.instance.pk,
                plexSourcePropertyMappingRequest: data,
            });
        }
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourcePlexCreate({
            plexSourcePropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-plex-form": PropertyMappingSourcePlexForm;
    }
}
