import "#components/ak-switch-input";
import "#elements/CodeMirror";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";
import { docLink } from "#common/global";

import { AKLabel } from "#components/ak-label";

import { BasePolicyForm } from "#admin/policies/BasePolicyForm";

import { ExpressionPolicy, PoliciesApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-policy-expression-form")
export class ExpressionPolicyForm extends BasePolicyForm<ExpressionPolicy> {
    loadInstance(pk: string): Promise<ExpressionPolicy> {
        return aki(PoliciesApi).policiesExpressionRetrieve({
            policyUuid: pk,
        });
    }

    async send(data: ExpressionPolicy): Promise<ExpressionPolicy> {
        if (this.instance) {
            return aki(PoliciesApi).policiesExpressionUpdate({
                policyUuid: this.instance.pk || "",
                expressionPolicyRequest: data,
            });
        }
        return aki(PoliciesApi).policiesExpressionCreate({
            expressionPolicyRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Executes the python snippet to determine whether to allow or deny a request.",
                )}
            </span>
            <ak-form-element-horizontal required name="name">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "name",
                        required: true,
                    },
                    msg("Name"),
                )}
                <input
                    id="name"
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-switch-input
                name="executionLogging"
                label=${msg("Execution logging")}
                ?checked=${this.instance?.executionLogging ?? false}
                help=${msg(
                    "When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.",
                )}
            >
            </ak-switch-input>
            <ak-form-group open label="${msg("Policy-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal required name="expression">
                        ${AKLabel(
                            {
                                slot: "label",
                                className: "pf-c-form__group-label",
                                htmlFor: "expression",
                                required: true,
                            },
                            msg("Expression"),
                        )}
                        <ak-codemirror
                            id="expression"
                            mode="python"
                            value="${ifDefined(this.instance?.expression)}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg("Expression using Python.")}
                            <a
                                rel="noopener noreferrer"
                                target="_blank"
                                href=${docLink("/customize/policies/expression")}
                            >
                                ${msg("See documentation for a list of all variables.")}
                            </a>
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-expression-form": ExpressionPolicyForm;
    }
}
