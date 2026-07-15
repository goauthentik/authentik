import "#components/ak-text-input";
import "#components/ak-number-input";
import "#components/ak-switch-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/HorizontalFormElement";
import "#components/ak-radio-input";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { RadioOption } from "#elements/forms/Radio";
import { SlottedTemplateResult } from "#elements/types";

import { eventTransportsProvider, eventTransportsSelector } from "#admin/events/RuleFormHelpers";

import { NotificationModeEnum, PamApi, PolicyBindingModelRequestRule } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit-html";
import { ifDefined } from "lit-html/directives/if-defined.js";
import { customElement, property } from "lit/decorators.js";

function createNotificationModeOptions(): RadioOption<NotificationModeEnum>[] {
    return [
        {
            value: NotificationModeEnum.All,
            label: msg("Everyone who can approve"),
            default: true,
            description: html`${msg(
                "Notify every individually-selected reviewer and every member of the selected reviewer groups.",
            )}`,
        },
        {
            value: NotificationModeEnum.Direct,
            label: msg("Only direct reviewers"),
            description: html`${msg(
                "Notify only the individually-selected reviewers, not reviewer group members.",
            )}`,
        },
        {
            value: NotificationModeEnum.RandomMinReviewers,
            label: msg("Random subset"),
            description: html`${msg(
                "Notify a random subset, sized to Minimum reviewers, of everyone who can approve.",
            )}`,
        },
    ];
}

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
            </ak-switch-input>
            <ak-form-element-horizontal
                label=${msg("Notification transports")}
                name="notificationTransports"
            >
                <ak-dual-select-dynamic-selected
                    .provider=${eventTransportsProvider}
                    .selector=${eventTransportsSelector(this.instance?.notificationTransports)}
                    available-label=${msg("Available Transports")}
                    selected-label=${msg("Selected Transports")}
                ></ak-dual-select-dynamic-selected>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Transports used to notify reviewers when a request is created. Leave empty to send no notification.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-radio-input
                label=${msg("Notify")}
                name="notificationMode"
                .options=${createNotificationModeOptions()}
                .value=${this.instance?.notificationMode}
            ></ak-radio-input>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-pbm-request-rule-form": PolicyBindingModelRequestRuleForm;
    }
}
