import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { docLink } from "@goauthentik/common/global";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { PropertymappingsApi, SAMLPropertyMapping } from "@goauthentik/api";

@customElement("ak-property-mapping-saml-form")
export class PropertyMappingSAMLForm extends ModelForm<SAMLPropertyMapping, string> {
    loadInstance(pk: string): Promise<SAMLPropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSamlRetrieve({
            pmUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated mapping.`;
        } else {
            return t`Successfully created mapping.`;
        }
    }

    async send(data: SAMLPropertyMapping): Promise<SAMLPropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSamlUpdate({
                pmUuid: this.instance.pk || "",
                sAMLPropertyMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsSamlCreate({
                sAMLPropertyMappingRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`SAML Attribute Name`}
                ?required=${true}
                name="samlName"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.samlName)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`Attribute name used for SAML Assertions. Can be a URN OID, a schema reference, or a any other string. If this property mapping is used for NameID Property, this field is discarded.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Friendly Name`} name="friendlyName">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.friendlyName || "")}"
                    class="pf-c-form-control"
                />
                <p class="pf-c-form__helper-text">
                    ${t`Optionally set the 'FriendlyName' value of the Assertion attribute.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Expression`} ?required=${true} name="expression">
                <ak-codemirror mode="python" value="${ifDefined(this.instance?.expression)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${t`Expression using Python.`}
                    <a
                        target="_blank"
                        href="${docLink("/docs/property-mappings/expression?utm_source=authentik")}"
                    >
                        ${t`See documentation for a list of all variables.`}
                    </a>
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }
}
