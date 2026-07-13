import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { KerberosSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-kerberos-form")
export class PropertyMappingSourceKerberosForm extends BasePropertyMappingForm<KerberosSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsSourceKerberosRetrieve({ pmUuid: pk }),
        create: (kerberosSourcePropertyMappingRequest: KerberosSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceKerberosCreate({
                kerberosSourcePropertyMappingRequest,
            }),
        update: (pk: string, kerberosSourcePropertyMappingRequest: KerberosSourcePropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsSourceKerberosUpdate({
                pmUuid: pk,
                kerberosSourcePropertyMappingRequest,
            }),
    };
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-kerberos-form": PropertyMappingSourceKerberosForm;
    }
}
