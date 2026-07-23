import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/HorizontalFormElement";
import "#admin/common/ak-flow-search/ak-flow-search";
import "#components/ak-text-input";
import "#components/ak-radio-input";
import "#components/ak-number-input";
import "#components/ak-switch-input";

import { aki } from "#common/api/client";

import { ModelForm } from "#elements/forms/ModelForm";
import { RadioOption } from "#elements/forms/Radio";
import { SlottedTemplateResult } from "#elements/types";

import { eventTransportsProvider, eventTransportsSelector } from "#admin/events/RuleFormHelpers";

import {
    FlowDesignationEnum,
    NotificationModeEnum,
    RequestRule,
    RequestsApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { ifDefined } from "lit-html/directives/if-defined.js";
import { customElement } from "lit/decorators.js";

function createNotificationModeOptions(): RadioOption<NotificationModeEnum>[] {
    return [
        {
            value: NotificationModeEnum.All,
            label: msg("Everyone who can approve"),
            default: true,
        },
        {
            value: NotificationModeEnum.Direct,
            label: msg("Only individually-selected reviewers"),
        },
        {
            value: NotificationModeEnum.RandomMinReviewers,
            label: msg("A random subset of size minimum reviewers, from everyone who can approve"),
        },
    ] satisfies RadioOption<NotificationModeEnum>[];
}

@customElement("ak-request-rule-form")
export class RequestRuleForm extends ModelForm<RequestRule, string> {
    public static override verboseName = msg("Request Rule");
    public static override verboseNamePlural = msg("Request Rules");

    protected async loadInstance(pk: string): Promise<RequestRule> {
        return aki(RequestsApi).requestsRulesRetrieve({ uuid: pk });
    }

    protected override async send(data: RequestRule): Promise<RequestRule> {
        if (this.instance?.uuid) {
            return aki(RequestsApi).requestsRulesUpdate({
                uuid: this.instance.uuid,
                requestRuleRequest: data,
            });
        }

        return aki(RequestsApi).requestsRulesCreate({
            requestRuleRequest: data,
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
                    "Number of reviewers that must approve the request before it is granted.",
                )}
            ></ak-number-input>
            <ak-switch-input
                name="minReviewersIsPerGroup"
                ?checked=${this.instance?.minReviewersIsPerGroup ?? false}
                label=${msg("Minimum reviewers is per-group")}
                .help=${msg(
                    html`If checked, fulfilling the request will require at least that many
                        reviewers from <em>each</em> of the reviewer groups bound to this rule. When
                        disabled, the value is a total across all reviewer groups.`,
                )}
            >
            </ak-switch-input>

            <ak-radio-input
                label=${msg("Notify")}
                name="notificationMode"
                .value=${this.instance?.notificationMode ?? NotificationModeEnum.All}
                .options=${createNotificationModeOptions()}
                help=${msg("Who to notify when a request is created against this rule.")}
            ></ak-radio-input>
            ${this.renderTransportsSelection()}

            <ak-form-element-horizontal label=${msg("Request flow")} name="requestFlow">
                <ak-flow-search
                    flowType=${FlowDesignationEnum.StageConfiguration}
                    .currentFlow=${this.instance?.requestFlow}
                ></ak-flow-search>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Optional flow to use when a user requests access to a target bound to this rule.",
                    )}
                </p>
            </ak-form-element-horizontal>`;
    }

    protected renderTransportsSelection(): SlottedTemplateResult {
        return html`
            <ak-form-element-horizontal
                label=${msg("Notification transports")}
                name="notificationTransports"
            >
                <ak-dual-select-dynamic-selected
                    .provider=${eventTransportsProvider}
                    .selector=${eventTransportsSelector(this.instance?.notificationTransports)}
                    available-label="${msg("Available Transports")}"
                    selected-label="${msg("Selected Transports")}"
                ></ak-dual-select-dynamic-selected>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Select which transports should be used to notify reviewers. If none are selected, the notification will only be shown in the authentik UI.",
                    )}
                </p>
            </ak-form-element-horizontal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-request-rule-form": RequestRuleForm;
    }
}
