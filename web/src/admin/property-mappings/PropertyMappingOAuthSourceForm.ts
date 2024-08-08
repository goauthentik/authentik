import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { OAuthSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-oauth-source-form")
export class PropertyMappingOAuthSourceForm extends BasePropertyMappingForm<OAuthSourcePropertyMapping> {
    docLink(): string {
        return "/docs/sources/property-mappings/expression?utm_source=authentik";
    }

    loadInstance(pk: string): Promise<OAuthSourcePropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceOauthRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: OAuthSourcePropertyMapping): Promise<OAuthSourcePropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceOauthUpdate({
                pmUuid: this.instance.pk,
                oAuthSourcePropertyMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceOauthCreate({
                oAuthSourcePropertyMappingRequest: data,
            });
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-oauth-source-form": PropertyMappingOAuthSourceForm;
    }
}
