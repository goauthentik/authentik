import "#admin/policies/conditional/ak-policy-action-builder";
import "#components/ak-switch-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";
import { PFSize } from "#common/enums";
import { APIError, findCause, HTTPStatusCode, isResponseErrorLike } from "#common/errors/network";
import { APIMessage } from "#common/messages";

import { BasePolicyForm } from "#admin/policies/BasePolicyForm";
import { pluckConditionErrors } from "#admin/policies/conditional/utils";

import {
    ConditionalPolicy,
    ConditionCatalog,
    MissingBehaviorEnum,
    PoliciesApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-policy-conditional-form")
export class ConditionalPolicyForm extends BasePolicyForm<ConditionalPolicy> {
    public static styles: CSSResult[] = [
        ...super.styles,
        css`
            /* The condition builder has no label and uses the full width of the form */
            ak-form-element-horizontal.actions::part(form-group) {
                grid-template-columns: 1fr;
            }
        `,
    ];

    @state()
    protected catalog?: ConditionCatalog;

    constructor() {
        super();
        // The action editor shows a side panel, which needs more space
        this.size = PFSize.XLarge;
    }

    protected endpoints = {
        load: (policyUuid: string) =>
            aki(PoliciesApi).policiesConditionalRetrieve({
                policyUuid,
            }),
        create: (conditionalPolicyRequest: ConditionalPolicy) =>
            aki(PoliciesApi).policiesConditionalCreate({
                conditionalPolicyRequest,
            }),
        update: (policyUuid: string, conditionalPolicyRequest: ConditionalPolicy) =>
            aki(PoliciesApi).policiesConditionalUpdate({
                policyUuid,
                conditionalPolicyRequest,
            }),
    };

    /**
     * Send the policy, and show validation errors of the actions on the actions they
     * belong to. The generic form only shows a summary for the whole field.
     */
    protected override async send(data: ConditionalPolicy): Promise<ConditionalPolicy> {
        const builder = this.renderRoot.querySelector("ak-policy-action-builder");

        if (builder) builder.errors = {};

        try {
            return await super.send(data);
        } catch (error) {
            const responseError = findCause(error, isResponseErrorLike);

            if (builder && responseError?.response.status === HTTPStatusCode.BadRequest) {
                // Read a copy, the form parses the response body as well
                const body: unknown = await responseError.response
                    .clone()
                    .json()
                    .catch(() => null);

                builder.errors = pluckConditionErrors(body);
            }

            throw error;
        }
    }

    /**
     * Errors of the actions are an object with a summary and errors per action, which the
     * generic form can't describe.
     */
    protected override formatAPIErrorMessage(error: APIError): APIMessage | null {
        const message = super.formatAPIErrorMessage(error);
        const actions: unknown = (error as Record<string, unknown>).actions;

        if (message && actions && typeof actions === "object" && "detail" in actions) {
            message.description = String(actions.detail);
        }

        return message;
    }

    protected override async load(): Promise<void> {
        this.catalog = await aki(PoliciesApi).policiesConditionalCatalogRetrieve();
    }

    protected override renderForm(): TemplateResult {
        return html`<span>
                ${msg(
                    "Checks conditions and sets values using the user, the request and the object being accessed, without writing code.",
                    { id: "policies.actions.form.description" },
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
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
                    <ak-form-element-horizontal class="actions" required name="actions">
                        <ak-policy-action-builder
                            name="actions"
                            .catalog=${this.catalog}
                            .value=${this.instance?.actions}
                            .labels=${this.instance?.labels}
                        ></ak-policy-action-builder>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("When a value is missing", {
                            id: "policies.conditional.missing-behavior.label",
                        })}
                        name="missingBehavior"
                    >
                        <select class="pf-c-form-control">
                            <option
                                value=${MissingBehaviorEnum.Fail}
                                ?selected=${
                                    this.instance?.missingBehavior !== MissingBehaviorEnum.False
                                }
                            >
                                ${msg("Fail the policy", {
                                    id: "policies.conditional.missing-behavior.fail",
                                })}
                            </option>
                            <option
                                value=${MissingBehaviorEnum.False}
                                ?selected=${
                                    this.instance?.missingBehavior === MissingBehaviorEnum.False
                                }
                            >
                                ${msg("Treat the condition as false", {
                                    id: "policies.conditional.missing-behavior.false",
                                })}
                            </option>
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Values can be missing when a variable is not available where the policy is used, for example prompt data outside of a flow. Use 'is set' conditions to check explicitly.",
                                { id: "policies.conditional.missing-behavior.help" },
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${msg("Failure message", {
                            id: "policies.conditional.failure-message.label",
                        })}
                        name="failureMessage"
                    >
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.failureMessage || "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Message shown to the user when the policy does not pass.", {
                                id: "policies.conditional.failure-message.help",
                            })}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-conditional-form": ConditionalPolicyForm;
    }
}
