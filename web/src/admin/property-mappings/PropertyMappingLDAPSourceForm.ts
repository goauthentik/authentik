import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { LDAPSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-ldap-source-form")
export class PropertyMappingLDAPSourceForm extends BasePropertyMappingForm<LDAPSourcePropertyMapping> {
    docLink(): string {
        return "/docs/sources/property-mappings/expression?utm_source=authentik";
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
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceLdapCreate({
                lDAPSourcePropertyMappingRequest: data,
            });
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-ldap-source-form": PropertyMappingLDAPSourceForm;
    }
}
