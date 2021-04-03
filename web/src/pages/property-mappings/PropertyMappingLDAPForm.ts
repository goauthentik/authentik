import { LDAPPropertyMapping, PropertymappingsApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";

@customElement("ak-property-mapping-ldap-form")
export class PropertyMappingLDAPForm extends Form<LDAPPropertyMapping> {

    set mappingUUID(value: string) {
        new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsLdapRead({
            pmUuid: value,
        }).then(mapping => {
            this.mapping = mapping;
        });
    }

    @property({attribute: false})
    mapping?: LDAPPropertyMapping;

    getSuccessMessage(): string {
        if (this.mapping) {
            return t`Successfully updated mapping.`;
        } else {
            return t`Successfully created mapping.`;
        }
    }

    send = (data: LDAPPropertyMapping): Promise<LDAPPropertyMapping> => {
        if (this.mapping) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsLdapUpdate({
                pmUuid: this.mapping.pk || "",
                data: data
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsLdapCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.mapping?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Object field`}
                ?required=${true}
                name="objectField">
                <input type="text" value="${ifDefined(this.mapping?.objectField)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${t`Field of the user object this value is written to.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Expression`}
                name="expression">
                <ak-codemirror mode="python" value="${ifDefined(this.mapping?.expression)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    Expression using Python. See <a href="https://goauthentik.io/docs/property-mappings/expression/">here</a> for a list of all variables.
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }

}
