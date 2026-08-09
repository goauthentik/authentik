import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { LDAPSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-ldap-form")
export class PropertyMappingSourceLDAPForm extends BasePropertyMappingForm<LDAPSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsSourceLdapRetrieve({ pmUuid: pk }),
        create: (lDAPSourcePropertyMappingRequest: LDAPSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceLdapCreate({
                lDAPSourcePropertyMappingRequest,
            }),
        update: (pk: string, lDAPSourcePropertyMappingRequest: LDAPSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceLdapUpdate({
                pmUuid: pk,
                lDAPSourcePropertyMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-ldap-form": PropertyMappingSourceLDAPForm;
    }
}
