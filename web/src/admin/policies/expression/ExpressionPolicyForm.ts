import { BasePolicyForm } from "@goauthentik/admin/policies/BasePolicyForm";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { docLink } from "@goauthentik/common/global";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/CodeMirror";
import { CodeMirrorMode } from "@goauthentik/elements/CodeMirror";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFTitle from "@patternfly/patternfly/components/Title/title.css";
import PFGrid from "@patternfly/patternfly/layouts/Grid/grid.css";

import { ExpressionPolicy, PoliciesApi } from "@goauthentik/api";

@customElement("ak-policy-expression-form")
export class ExpressionPolicyForm extends BasePolicyForm<ExpressionPolicy> {

    @property({type: Boolean})
    showPreview = true;

    static get styles(): CSSResult[] {
        return super.styles.concat(PFGrid, PFTitle);
    }

    loadInstance(pk: string): Promise<ExpressionPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesExpressionRetrieve({
            policyUuid: pk,
        });
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
        return html`<div class="pf-l-grid pf-m-gutter">
            <div class="pf-l-grid__item pf-m-6-col pf-c-form pf-m-horizontal">
                ${this.renderEditForm()}
            </div>
            <div class="pf-l-grid__item pf-m-6-col">${this.renderPreview()}</div>
        </div> `;
    }

    renderPreview(): TemplateResult {
        return html`
            <h3 class="pf-c-title pf-m-lg">${msg("Preview")}</h3>
            <div class="pf-l-grid pf-m-gutter">
                <div class="pf-c-card pf-m-selectable pf-m-selected pf-l-grid__item pf-m-12-col">
                    <div class="pf-c-card__body"></div>
                </div>
            </div>
        `;
    }

    renderEditForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Executes the Python snippet to determine whether to allow or deny a request.",
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
                            mode=${CodeMirrorMode.Python}
                            value="${ifDefined(this.instance?.expression)}"
                        >
                        </ak-codemirror>
                        <p class="pf-c-form__helper-text">
                            ${msg("Expression using Python.")}
                            <a
                                rel="noopener noreferrer"
                                target="_blank"
                                href="${docLink(
                                    "/docs/customize/policies/expression?utm_source=authentik",
                                )}"
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
