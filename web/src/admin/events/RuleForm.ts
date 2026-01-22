import "#components/ak-switch-input";
import "#elements/ak-dual-select/ak-dual-select-dynamic-selected-provider";
import "#elements/forms/HorizontalFormElement";
import "#elements/forms/Radio";
import "#elements/forms/SearchSelect/index";

import { eventTransportsProvider, eventTransportsSelector } from "./RuleFormHelpers.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { severityToLabel } from "#common/labels";

import { ModelForm } from "#elements/forms/ModelForm";
import { RadioOption } from "#elements/forms/Radio";

import {
    CoreApi,
    CoreGroupsListRequest,
    EventsApi,
    Group,
    NotificationRule,
    PaginatedNotificationTransportList,
    SeverityEnum,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-event-rule-form")
export class RuleForm extends ModelForm<NotificationRule, string> {
    eventTransports?: PaginatedNotificationTransportList;

    loadInstance(pk: string): Promise<NotificationRule> {
        return new EventsApi(DEFAULT_CONFIG).eventsRulesRetrieve({
            pbmUuid: pk,
        });
    }

    async load(): Promise<void> {
        this.eventTransports = await new EventsApi(DEFAULT_CONFIG).eventsTransportsList({
            ordering: "name",
        });
    }

    getSuccessMessage(): string {
        return this.instance
            ? msg("Successfully updated rule.")
            : msg("Successfully created rule.");
    }

    async send(data: NotificationRule): Promise<NotificationRule> {
        if (this.instance) {
            return new EventsApi(DEFAULT_CONFIG).eventsRulesUpdate({
                pbmUuid: this.instance.pk || "",
                notificationRuleRequest: data,
            });
        }
        return new EventsApi(DEFAULT_CONFIG).eventsRulesCreate({
            notificationRuleRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html` <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Group")} name="destinationGroup">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Group[]> => {
                        const args: CoreGroupsListRequest = {
                            ordering: "name",
                            includeUsers: false,
                        };

                        if (query !== undefined) {
                            args.search = query;
                        }

                        const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(args);

                        return groups.results;
                    }}
                    .renderElement=${(group: Group) => group.name}
                    .value=${(group: Group | null) => group?.pk}
                    .selected=${(group: Group): boolean => {
                        return group.pk === this.instance?.destinationGroup;
                    }}
                    blankable
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg("Select the group of users which the alerts are sent to. ")}
                </p>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "If no group is selected and 'Send notification to event user' is disabled the rule is disabled. ",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-switch-input
                name="destinationEventUser"
                label=${msg("Send notification to event user")}
                ?checked=${this.instance?.destinationEventUser ?? false}
                help=${msg(
                    "When enabled, notification will be sent to the user that triggered the event in addition to any users in the group above. The event user will always be the first user, to send a notification only to the event user enabled 'Send once' in the notification transport. If no group is selected and 'Send notification to event user' is disabled the rule is disabled. ",
                )}
            >
            </ak-switch-input>
            <ak-form-element-horizontal label=${msg("Transports")} required name="transports">
                <ak-dual-select-dynamic-selected
                    .provider=${eventTransportsProvider}
                    .selector=${eventTransportsSelector(this.instance?.transports)}
                    available-label="${msg("Available Transports")}"
                    selected-label="${msg("Selected Transports")}"
                ></ak-dual-select-dynamic-selected>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Select which transports should be used to notify the user. If none are selected, the notification will only be shown in the authentik UI.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Severity")} required name="severity">
                <ak-radio
                    .options=${[
                        {
                            label: severityToLabel(SeverityEnum.Alert),
                            value: SeverityEnum.Alert,
                            default: true,
                        },
                        {
                            label: severityToLabel(SeverityEnum.Warning),
                            value: SeverityEnum.Warning,
                        },
                        {
                            label: severityToLabel(SeverityEnum.Notice),
                            value: SeverityEnum.Notice,
                        },
                    ] satisfies RadioOption<SeverityEnum>[]}
                    .value=${this.instance?.severity}
                >
                </ak-radio>
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-event-rule-form": RuleForm;
    }
}
