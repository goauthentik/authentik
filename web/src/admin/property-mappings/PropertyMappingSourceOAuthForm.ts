import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { OAuthSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-oauth-form")
export class PropertyMappingSourceOAuthForm extends BasePropertyMappingForm<OAuthSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsSourceOauthRetrieve({ pmUuid: pk }),
        create: (oAuthSourcePropertyMappingRequest: OAuthSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceOauthCreate({
                oAuthSourcePropertyMappingRequest,
            }),
        update: (pk: string, oAuthSourcePropertyMappingRequest: OAuthSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceOauthUpdate({
                pmUuid: pk,
                oAuthSourcePropertyMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-oauth-form": PropertyMappingSourceOAuthForm;
    }
}
