import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { LDAPSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-source-ldap-form")
export class PropertyMappingSourceLDAPForm extends BasePropertyMappingForm<LDAPSourcePropertyMapping> {
    docLink(): string {
        return "/docs/users-sources/sources/property-mappings/expressions?utm_source=authentik";
    }

    loadInstance(pk: string): Promise<LDAPSourcePropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceLdapRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: LDAPSourcePropertyMapping): Promise<LDAPSourcePropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceLdapUpdate({
                pmUuid: this.instance.pk,
                lDAPSourcePropertyMappingRequest: data,
            });
        }
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceLdapCreate({
            lDAPSourcePropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-ldap-form": PropertyMappingSourceLDAPForm;
    }
}
