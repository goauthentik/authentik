import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, SAMLSourcePropertyMapping } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-saml-form")
export class PropertyMappingSourceSAMLForm extends BasePropertyMappingForm<SAMLSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    loadInstance(pk: string): Promise<SAMLSourcePropertyMapping> {
        return aki(PropertymappingsApi).propertymappingsSourceSamlRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: SAMLSourcePropertyMapping): Promise<SAMLSourcePropertyMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsSourceSamlUpdate({
                pmUuid: this.instance.pk,
                sAMLSourcePropertyMappingRequest: data,
            });
        }
        return aki(PropertymappingsApi).propertymappingsSourceSamlCreate({
            sAMLSourcePropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-saml-form": PropertyMappingSourceSAMLForm;
    }
}
