import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { docLink } from "@goauthentik/common/global";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import { ExpressionPolicy, PoliciesApi } from "@goauthentik/api";

@customElement("ak-policy-expression-form")
export class ExpressionPolicyForm extends ModelForm<ExpressionPolicy, string> {
    loadInstance(pk: string): Promise<ExpressionPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesExpressionRetrieve({
            policyUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated policy.");
        } else {
            return msg("Successfully created policy.");
        }
    }

    async send(data: ExpressionPolicy): Promise<ExpressionPolicy> {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesExpressionUpdate({
                policyUuid: this.instance.pk || "",
                expressionPolicyRequest: data,
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesExpressionCreate({
                expressionPolicyRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <span>
                ${msg(
                    "Executes the python snippet to determine whether to allow or deny a request.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="executionLogging">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.executionLogging, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Execution logging")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Policy-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${msg("Expression")}
                        ?required=${true}
                        name="expression"
                    >
                        <ak-codemirror
                            mode="python"
                            value="${ifDefined(this.instance?.expression)}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg("Expression using Python.")}
                            <a
                                target="_blank"
                                href="${docLink("/docs/policies/expression?utm_source=authentik")}"
                            >
                                ${msg("See documentation for a list of all variables.")}
                            </a>
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
