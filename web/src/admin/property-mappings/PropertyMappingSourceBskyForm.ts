import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { BskySourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-bsky-form")
export class PropertyMappingSourceBskyForm extends BasePropertyMappingForm<BskySourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsSourceBskyRetrieve({ pmUuid: pk }),
        create: (bskySourcePropertyMappingRequest: BskySourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceBskyCreate({
                bskySourcePropertyMappingRequest,
            }),
        update: (pk: string, bskySourcePropertyMappingRequest: BskySourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceBskyUpdate({
                pmUuid: pk,
                bskySourcePropertyMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-bsky-form": PropertyMappingSourceBskyForm;
    }
}
