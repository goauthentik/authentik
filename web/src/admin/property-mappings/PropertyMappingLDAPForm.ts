import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { docLink } from "@goauthentik/common/global";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { LDAPPropertyMapping, PropertymappingsApi } from "@goauthentik/api";

@customElement("ak-property-mapping-ldap-form")
export class PropertyMappingLDAPForm extends ModelForm<LDAPPropertyMapping, string> {
    loadInstance(pk: string): Promise<LDAPPropertyMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsLdapRetrieve({
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

    async send(data: LDAPPropertyMapping): Promise<LDAPPropertyMapping> {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsLdapUpdate({
                pmUuid: this.instance.pk || "",
                lDAPPropertyMappingRequest: data,
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsLdapCreate({
                lDAPPropertyMappingRequest: data,
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
                label=${t`Object field`}
                ?required=${true}
                name="objectField"
            >
                <input
                    type="text"
                    value="${ifDefined(this.instance?.objectField)}"
                    class="pf-c-form-control"
                    required
                />
                <p class="pf-c-form__helper-text">
                    ${t`Field of the user object this value is written to.`}
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
