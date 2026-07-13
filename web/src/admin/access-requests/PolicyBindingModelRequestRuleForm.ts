import "#components/ak-text-input";
import "../../components/ak-number-input";
import "../../components/ak-switch-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { SlottedTemplateResult } from "#elements/types";

import {
    reviewerGroupsProvider,
    reviewerGroupsSelector,
    reviewerUsersProvider,
    reviewerUsersSelector,
} from "#admin/access-requests/RequestRuleFormHelpers";

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
            <ak-form-element-horizontal label=${msg("Reviewer groups")} name="reviewerGroups">
                <ak-dual-select-dynamic-selected
                    .provider=${reviewerGroupsProvider}
                    .selector=${reviewerGroupsSelector(this.instance?.reviewerGroups)}
                    available-label=${msg("Available Groups")}
                    selected-label=${msg("Selected Groups")}
                ></ak-dual-select-dynamic-selected>
            </ak-form-element-horizontal>
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
            </ak-switch-input>
            <ak-form-element-horizontal label=${msg("Reviewers")} name="reviewers">
                <ak-dual-select-dynamic-selected
                    .provider=${reviewerUsersProvider}
                    .selector=${reviewerUsersSelector(this.instance?.reviewers)}
                    available-label=${msg("Available Users")}
                    selected-label=${msg("Selected Users")}
                ></ak-dual-select-dynamic-selected>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "A request will additionally be approvable by each of the users selected here, on top of the reviewer groups above.",
                    )}
                </p>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-pbm-request-rule-form": PolicyBindingModelRequestRuleForm;
    }
}
