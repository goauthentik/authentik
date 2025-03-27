import { BasePropertyMappingForm } from "@goauthentik/admin/property-mappings/BasePropertyMappingForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { customElement } from "lit/decorators.js";

import { KerberosSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-source-kerberos-form")
export class PropertyMappingSourceKerberosForm extends BasePropertyMappingForm<KerberosSourcePropertyMapping> {
    docLink(): string {
        return "/docs/sources/property-mappings/expressions?utm_source=authentik";
    }

    loadInstance(pk: string): Promise<KerberosSourcePropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceKerberosRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: KerberosSourcePropertyMapping): Promise<KerberosSourcePropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceKerberosUpdate({
                pmUuid: this.instance.pk,
                kerberosSourcePropertyMappingRequest: data,
            });
        }
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceKerberosCreate({
            kerberosSourcePropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-kerberos-form": PropertyMappingSourceKerberosForm;
    }
}
