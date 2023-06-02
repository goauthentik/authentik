import { SeverityToLabel } from "@goauthentik/admin/events/utils";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/Radio";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    CoreApi,
    CoreGroupsListRequest,
    EventsApi,
    Group,
    NotificationRule,
    PaginatedNotificationTransportList,
    SeverityEnum,
} from "@goauthentik/api";

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
        if (this.instance) {
            return msg("Successfully updated rule.");
        } else {
            return msg("Successfully created rule.");
        }
    }

    async send(data: NotificationRule): Promise<NotificationRule> {
        if (this.instance) {
            return new EventsApi(DEFAULT_CONFIG).eventsRulesUpdate({
                pbmUuid: this.instance.pk || "",
                notificationRuleRequest: data,
            });
        } else {
            return new EventsApi(DEFAULT_CONFIG).eventsRulesCreate({
                notificationRuleRequest: data,
            });
        }
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Group")} name="group">
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<Group[]> => {
                        const args: CoreGroupsListRequest = {
                            ordering: "name",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const groups = await new CoreApi(DEFAULT_CONFIG).coreGroupsList(args);
                        return groups.results;
                    }}
                    .renderElement=${(group: Group): string => {
                        return group.name;
                    }}
                    .value=${(group: Group | undefined): string | undefined => {
                        return group?.pk;
                    }}
                    .selected=${(group: Group): boolean => {
                        return group.pk === this.instance?.group;
                    }}
                    ?blankable=${true}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Select the group of users which the alerts are sent to. If no group is selected the rule is disabled.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${msg("Transports")}
                ?required=${true}
                name="transports"
            >
                <select class="pf-c-form-control" multiple>
                    ${this.eventTransports?.results.map((transport) => {
                        const selected = Array.from(this.instance?.transports || []).some((su) => {
                            return su == transport.pk;
                        });
                        return html`<option value=${ifDefined(transport.pk)} ?selected=${selected}>
                            ${transport.name}
                        </option>`;
                    })}
                </select>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "Select which transports should be used to notify the user. If none are selected, the notification will only be shown in the authentik UI.",
                    )}
                </p>
                <p class="pf-c-form__helper-text">
                    ${msg("Hold control/command to select multiple items.")}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${msg("Severity")} ?required=${true} name="severity">
                <ak-radio
                    .options=${[
                        {
                            label: SeverityToLabel(SeverityEnum.Alert),
                            value: SeverityEnum.Alert,
                            default: true,
                        },
                        {
                            label: SeverityToLabel(SeverityEnum.Warning),
                            value: SeverityEnum.Warning,
                        },
                        {
                            label: SeverityToLabel(SeverityEnum.Notice),
                            value: SeverityEnum.Notice,
                        },
                    ]}
                    .value=${this.instance?.severity}
                >
                </ak-radio>
            </ak-form-element-horizontal>
        </form>`;
    }
}
