import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { KerberosSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-kerberos-form")
export class PropertyMappingSourceKerberosForm extends BasePropertyMappingForm<KerberosSourcePropertyMapping> {
    public override docLink(): string {
        return "/docs/sources/property-mappings/expressions?utm_source=authentik";
    }

    protected loadInstance(pk: string): Promise<KerberosSourcePropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSourceKerberosRetrieve({
            pmUuid: pk,
        });
    }

    protected async send(
        data: KerberosSourcePropertyMapping,
    ): Promise<KerberosSourcePropertyMapping> {
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
