import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { customElement } from "lit/decorators.js";

import { OAuthSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-oauth-source-form")
export class PropertyMappingOAuthForm extends BasePropertyMappingForm<OAuthSourcePropertyMapping> {
    loadInstance(pk: string): Promise<OAuthSourcePropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsOauthSourceRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: OAuthSourcePropertyMapping): Promise<OAuthSourcePropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsOauthSourceUpdate({
                pmUuid: this.instance.pk || "",
                oAuthSourcePropertyMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsOauthSourceCreate({
                oAuthSourcePropertyMappingRequest: data,
            });
        }
    }
}
