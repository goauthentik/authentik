import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PlexSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-plex-form")
export class PropertyMappingSourcePlexForm extends BasePropertyMappingForm<PlexSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    loadInstance(pk: string): Promise<PlexSourcePropertyMapping> {
        return aki(PropertymappingsApi).propertymappingsSourcePlexRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: PlexSourcePropertyMapping): Promise<PlexSourcePropertyMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsSourcePlexUpdate({
                pmUuid: this.instance.pk,
                plexSourcePropertyMappingRequest: data,
            });
        }
        return aki(PropertymappingsApi).propertymappingsSourcePlexCreate({
            plexSourcePropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-plex-form": PropertyMappingSourcePlexForm;
    }
}
