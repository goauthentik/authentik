import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { KerberosSourcePropertyMapping, PropertymappingsApi } from "@goauthentik/api";

import { customElement } from "lit/decorators.js";

@customElement("ak-property-mapping-source-kerberos-form")
export class PropertyMappingSourceKerberosForm extends BasePropertyMappingForm<KerberosSourcePropertyMapping> {
    protected override docLink = "/users-sources/sources/property-mappings/expressions";

    loadInstance(pk: string): Promise<KerberosSourcePropertyMapping> {
        return aki(PropertymappingsApi).propertymappingsSourceKerberosRetrieve({
            pmUuid: pk,
        });
    }

    async send(data: KerberosSourcePropertyMapping): Promise<KerberosSourcePropertyMapping> {
        if (this.instance) {
            return aki(PropertymappingsApi).propertymappingsSourceKerberosUpdate({
                pmUuid: this.instance.pk,
                kerberosSourcePropertyMappingRequest: data,
            });
        }

        return aki(PropertymappingsApi).propertymappingsSourceKerberosCreate({
            kerberosSourcePropertyMappingRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-source-kerberos-form": PropertyMappingSourceKerberosForm;
    }
}
