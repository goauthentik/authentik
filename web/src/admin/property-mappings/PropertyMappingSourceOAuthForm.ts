import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { OAuthSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-oauth-form")
export class PropertyMappingSourceOAuthForm extends BasePropertyMappingForm<OAuthSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    loadInstance(pk: string): Promise<OAuthSourcePropertyMapping> {
        return aki(PropertymappingsApi).propertymappingsSourceOauthRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: OAuthSourcePropertyMapping): Promise<OAuthSourcePropertyMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsSourceOauthUpdate({
                pmUuid: this.instance.pk,
                oAuthSourcePropertyMappingRequest: data,
            });
        }
        return aki(PropertymappingsApi).propertymappingsSourceOauthCreate({
            oAuthSourcePropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-oauth-form": PropertyMappingSourceOAuthForm;
    }
}
