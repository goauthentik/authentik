import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { LDAPSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-ldap-form")
export class PropertyMappingSourceLDAPForm extends BasePropertyMappingForm<LDAPSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    loadInstance(pk: string): Promise<LDAPSourcePropertyMapping> {
        return aki(PropertymappingsApi).propertymappingsSourceLdapRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: LDAPSourcePropertyMapping): Promise<LDAPSourcePropertyMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsSourceLdapUpdate({
                pmUuid: this.instance.pk,
                lDAPSourcePropertyMappingRequest: data,
            });
        }
        return aki(PropertymappingsApi).propertymappingsSourceLdapCreate({
            lDAPSourcePropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-ldap-form": PropertyMappingSourceLDAPForm;
    }
}
