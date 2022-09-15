import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { CoreApi, EventsApi, NotificationRule, SeverityEnum } from "@goauthentik/api";

@customElement("ak-event-rule-form")
export class RuleForm extends ModelForm<NotificationRule, string> {
    loadInstance(pk: string): Promise<NotificationRule> {
        return new EventsApi(DEFAULT_CONFIG).eventsRulesRetrieve({
            pbmUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated rule.`;
        } else {
            return t`Successfully created rule.`;
        }
    }

    send = (data: NotificationRule): Promise<NotificationRule> => {
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
    };

    renderSeverity(): TemplateResult {
        return html`
            <option
                value=${SeverityEnum.Alert}
                ?selected=${this.instance?.severity === SeverityEnum.Alert}
            >
                ${t`Alert`}
            </option>
            <option
                value=${SeverityEnum.Warning}
                ?selected=${this.instance?.severity === SeverityEnum.Warning}
            >
                ${t`Warning`}
            </option>
            <option
                value=${SeverityEnum.Notice}
                ?selected=${this.instance?.severity === SeverityEnum.Notice}
            >
                ${t`Notice`}
            </option>
        `;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name)}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Group`} name="group">
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.instance?.group === undefined}>
                        ---------
                    </option>
                    ${until(
                        new CoreApi(DEFAULT_CONFIG).coreGroupsList({}).then((groups) => {
                            return groups.results.map((group) => {
                                return html`<option
                                    value=${ifDefined(group.pk)}
                                    ?selected=${this.instance?.group === group.pk}
                                >
                                    ${group.name}
                                </option>`;
                            });
                        }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Transports`} ?required=${true} name="transports">
                <select name="users" class="pf-c-form-control" multiple>
                    ${until(
                        new EventsApi(DEFAULT_CONFIG)
                            .eventsTransportsList({})
                            .then((transports) => {
                                return transports.results.map((transport) => {
                                    const selected = Array.from(
                                        this.instance?.transports || [],
                                    ).some((su) => {
                                        return su == transport.pk;
                                    });
                                    return html`<option
                                        value=${ifDefined(transport.pk)}
                                        ?selected=${selected}
                                    >
                                        ${transport.name}
                                    </option>`;
                                });
                            }),
                        html`<option>${t`Loading...`}</option>`,
                    )}
                </select>
                <p class="pf-c-form__helper-text">
                    ${t`Select which transports should be used to notify the user. If none are selected, the notification will only be shown in the authentik UI.`}
                </p>
                <p class="pf-c-form__helper-text">
                    ${t`Hold control/command to select multiple items.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal label=${t`Severity`} ?required=${true} name="severity">
                <select class="pf-c-form-control">
                    ${this.renderSeverity()}
                </select>
            </ak-form-element-horizontal>
        </form>`;
    }
}
