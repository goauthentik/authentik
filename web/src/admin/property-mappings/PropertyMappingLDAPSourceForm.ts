import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { customElement } from "lit/decorators.js";

import { LDAPSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-ldap-source-form")
export class PropertyMappingLDAPForm extends BasePropertyMappingForm<LDAPSourcePropertyMapping> {
    loadInstance(pk: string): Promise<LDAPSourcePropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsLdapSourceRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: LDAPSourcePropertyMapping): Promise<LDAPSourcePropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsLdapSourceUpdate({
                pmUuid: this.instance.pk || "",
                lDAPSourcePropertyMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsLdapSourceCreate({
                lDAPSourcePropertyMappingRequest: data,
            });
        }
    }
}
