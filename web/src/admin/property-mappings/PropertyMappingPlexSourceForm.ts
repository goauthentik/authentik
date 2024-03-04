import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";

import { customElement } from "lit/decorators.js";

import { PropertymappingsApi, SAMLSourcePropertyMapping } from "@goauthentik/api";

@customElement("ak-property-mapping-saml-source-form")
export class PropertyMappingSAMLForm extends BasePropertyMappingForm<SAMLSourcePropertyMapping> {
    loadInstance(pk: string): Promise<SAMLSourcePropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSamlSourceRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: SAMLSourcePropertyMapping): Promise<SAMLSourcePropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSamlSourceUpdate({
                pmUuid: this.instance.pk || "",
                sAMLSourcePropertyMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSamlSourceCreate({
                sAMLSourcePropertyMappingRequest: data,
            });
        }
    }
}
