import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { PropertymappingsApi, SAMLSourcePropertyMapping } from "@goauthentik/api";

@customElement("ak-property-mapping-saml-source-form")
export class PropertyMappingSAMLSourceForm extends BasePropertyMappingForm<SAMLSourcePropertyMapping> {
    docLink(): string {
        return "/docs/sources/property-mappings/expression?utm_source=authentik";
    }

    loadInstance(pk: string): Promise<SAMLSourcePropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceSamlRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: SAMLSourcePropertyMapping): Promise<SAMLSourcePropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceSamlUpdate({
                pmUuid: this.instance.pk,
                sAMLSourcePropertyMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceSamlCreate({
                sAMLSourcePropertyMappingRequest: data,
            });
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-saml-source-form": PropertyMappingSAMLSourceForm;
    }
}
