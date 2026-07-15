import "#components/ak-text-input";
import "../../components/ak-number-input";
import "../../components/ak-switch-input";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { PamApi, PolicyBindingModelRequestRule } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { ifDefined } from "lit-html/directives/if-defined.js";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-pbm-request-rule-form")
export class PolicyBindingModelRequestRuleForm extends ModelForm<
    PolicyBindingModelRequestRule,
    string
> {
    public static override verboseName = msg("Request Rule");
    public static override verboseNamePlural = msg("Request Rules");

    @property()
    pbmUuid?: string;

    protected async loadInstance(pk: string): Promise<PolicyBindingModelRequestRule | null> {
        return aki(PamApi).pamRequestRulesRetrieve({
            uuid: pk,
        });
    }

    protected override async send(
        data: PolicyBindingModelRequestRule,
    ): Promise<PolicyBindingModelRequestRule> {
        if (this.instance) {
            return aki(PamApi).pamRequestRulesUpdate({
                uuid: this.instance.uuid!,
                policyBindingModelRequestRuleRequest: data,
            });
        }
        data.pbm = this.pbmUuid!;
        return aki(PamApi).pamRequestRulesCreate({
            policyBindingModelRequestRuleRequest: data,
        });
    }

    protected renderForm(): SlottedTemplateResult {
        return html`<ak-text-input
                label=${msg("Rule Name")}
                name="name"
                required
                value="${ifDefined(this.instance?.name)}"
                placeholder=${msg("Type a name for this request rule...")}
            ></ak-text-input>
            <ak-number-input
                label=${msg("Minimum reviewers")}
                min=${1}
                name="minReviewers"
                value="${this.instance?.minReviewers ?? 1}"
                help=${msg(
                    "Number of users from the selected reviewer groups that must approve the request.",
                )}
            ></ak-number-input>
            <ak-switch-input
                name="minReviewersIsPerGroup"
                ?checked=${this.instance?.minReviewersIsPerGroup ?? false}
                label=${msg("Minimum reviewers is per-group")}
                .help=${msg(
                    html`If checked, approving a review will require at least that many users from
                        <em>each</em> of the selected groups. When disabled, the value is a total
                        across all groups.`,
                )}
            >
            </ak-switch-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-pbm-request-rule-form": PolicyBindingModelRequestRuleForm;
    }
}
