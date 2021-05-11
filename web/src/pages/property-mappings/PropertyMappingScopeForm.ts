import { ScopeMapping, PropertymappingsApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { ModelForm } from "../../elements/forms/ModelForm";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import "../../elements/CodeMirror";

@customElement("ak-property-mapping-scope-form")
export class PropertyMappingScopeForm extends ModelForm<ScopeMapping, string> {

    loadInstance(pk: string): Promise<ScopeMapping> {
        return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsScopeRead({
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

    send = (data: ScopeMapping): Promise<ScopeMapping> => {
        if (this.instance) {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsScopeUpdate({
                pmUuid: this.instance.pk || "",
                data: data
            });
        } else {
            return new PropertymappingsApi(DEFAULT_CONFIG).propertymappingsScopeCreate({
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
                <input type="text" value="${ifDefined(this.instance?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Scope name`}
                ?required=${true}
                name="scopeName">
                <input type="text" value="${ifDefined(this.instance?.scopeName)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${t`Scope which the client can specify to access these properties.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Description`}
                ?required=${true}
                name="description">
                <input type="text" value="${ifDefined(this.instance?.description)}" class="pf-c-form-control" required>
                <p class="pf-c-form__helper-text">${t`Description shown to the user when consenting. If left empty, the user won't be informed.`}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${t`Expression`}
                ?required=${true}
                name="expression">
                <ak-codemirror mode="python" value="${ifDefined(this.instance?.expression)}">
                </ak-codemirror>
                <p class="pf-c-form__helper-text">
                    ${t`Expression using Python.`}
                    <a target="_blank" href="https://goauthentik.io/docs/property-mappings/expression/">
                        ${t`See documentation for a list of all variables.`}
                    </a>
                </p>
            </ak-form-element-horizontal>
        </form>`;
    }

}
