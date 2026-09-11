import "#elements/CodeMirror";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { BasePropertyMappingForm } from "#admin/property-mappings/BasePropertyMappingForm";

import { PropertymappingsApi, SAMLPropertyMapping } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-property-mapping-provider-saml-form")
export class PropertyMappingProviderSAMLForm extends BasePropertyMappingForm<SAMLPropertyMapping> {
    protected endpoints = {
        load: (pk: string) =>
            aki(PropertymappingsApi).propertymappingsProviderSamlRetrieve({ pmUuid: pk }),
        create: (sAMLPropertyMappingRequest: SAMLPropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsProviderSamlCreate({
                sAMLPropertyMappingRequest,
            }),
        update: (pk: string, sAMLPropertyMappingRequest: SAMLPropertyMapping) =>
            aki(PropertymappingsApi).propertymappingsProviderSamlUpdate({
                pmUuid: pk,
                sAMLPropertyMappingRequest,
            }),
    };

    renderExtraFields(): TemplateResult {
        return html` <ak-form-element-horizontal
                label=${msg("SAML Attribute Name")}
                required
                name="samlName"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.samlName)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Attribute name used for SAML Assertions. Can be a URN OID, a schema reference, or a any other string. If this property mapping is used for NameID Property, this field is discarded.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Friendly Name")} name="friendlyName">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.friendlyName || "")}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${msg("Optionally set the 'FriendlyName' value of the Assertion attribute.")}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-property-mapping-provider-saml-form": PropertyMappingProviderSAMLForm;
    }
}
