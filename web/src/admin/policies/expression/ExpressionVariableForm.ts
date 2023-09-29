import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { ExpressionVariable, PoliciesApi } from "@goauthentik/api";

@customElement("ak-expression-variable-form")
export class ExpressionVariableForm extends ModelForm<ExpressionVariable, number> {
    loadInstance(pk: number): Promise<ExpressionVariable> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesExpressionVariablesRetrieve({
            id: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated variable.");
        } else {
            return msg("Successfully created variable.");
        }
    }

    async send(data: ExpressionVariable): Promise<ExpressionVariable> {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesExpressionVariablesUpdate({
                id: this.instance.id || 0,
                expressionVariableRequest: data,
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesExpressionVariablesCreate({
                expressionVariableRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <span> ${msg("Variable that can be passed to an expression policy")} </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Value")} ?required=${true} name="value">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.value || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
        </form>`;
    }
}
