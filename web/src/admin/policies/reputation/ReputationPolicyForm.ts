import "#components/ak-switch-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";

import { DEFAULT_CONFIG } from "#common/api/config";

import { BasePolicyForm } from "#admin/policies/BasePolicyForm";

import { PoliciesApi, ReputationPolicy } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-policy-reputation-form")
export class ReputationPolicyForm extends BasePolicyForm<ReputationPolicy> {
    loadInstance(pk: string): Promise<ReputationPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesReputationRetrieve({
            policyUuid: pk,
        });
    }

    async send(data: ReputationPolicy): Promise<ReputationPolicy> {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesReputationUpdate({
                policyUuid: this.instance.pk || "",
                reputationPolicyRequest: data,
            });
        }
        return new PoliciesApi(DEFAULT_CONFIG).policiesReputationCreate({
            reputationPolicyRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg("Allows/denys requests based on the users and/or the IPs reputation.")}
            </span>
            <span>
                ${msg(
                    `Invalid login attempts will decrease the score for the client's IP, and the
username they are attempting to login as, by one.`,
                )}
            </span>
            <span>
                ${msg(
                    `The policy passes when the reputation score is below the threshold, and
doesn't pass when either or both of the selected options are equal or above the threshold.`,
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
                    <ak-switch-input
                        name="checkIp"
                        label=${msg("Check IP")}
                        ?checked=${this.instance?.checkIp ?? true}
                    >
                    </ak-switch-input>
                    <ak-switch-input
                        name="checkUsername"
                        label=${msg("Check Username")}
                        ?checked=${this.instance?.checkUsername ?? false}
                    >
                    </ak-switch-input>
                    <ak-form-element-horizontal label=${msg("Threshold")} required name="threshold">
                        <input
                            type="number"
                            value="${ifDefined(this.instance?.threshold || -5)}"
                            class="pf-c-form-control"
                            required
                        />
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-reputation-form": ReputationPolicyForm;
    }
}
