import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { PlexSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-source-plex-form")
export class PropertyMappingSourcePlexForm extends BasePropertyMappingForm<PlexSourcePropertyMapping> {
    docLink(): string {
        return "/docs/users-sources/sources/property-mappings/expressions?utm_source=authentik";
    }

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
