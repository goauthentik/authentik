import { CoreApi, EventsApi, NotificationRule, NotificationRuleSeverityEnum } from "authentik-api";
import { gettext } from "django";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../api/Config";
import { Form } from "../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../elements/forms/HorizontalFormElement";
import { until } from "lit-html/directives/until";

@customElement("ak-event-rule-form")
export class RuleForm extends Form<NotificationRule> {

    @property({attribute: false})
    rule?: NotificationRule;

    getSuccessMessage(): string {
        if (this.rule) {
            return gettext("Successfully updated rule.");
        } else {
            return gettext("Successfully created rule.");
        }
    }

    send = (data: NotificationRule): Promise<NotificationRule> => {
        if (this.rule) {
            return new EventsApi(DEFAULT_CONFIG).eventsRulesUpdate({
                pbmUuid: this.rule.pk || "",
                data: data
            });
        } else {
            return new EventsApi(DEFAULT_CONFIG).eventsRulesCreate({
                data: data
            });
        }
    };

    renderSeverity(): TemplateResult {
        return html`
            <option value=${NotificationRuleSeverityEnum.Alert} ?selected=${this.rule?.severity === NotificationRuleSeverityEnum.Alert}>
                ${gettext("Alert")}
            </option>
            <option value=${NotificationRuleSeverityEnum.Warning} ?selected=${this.rule?.severity === NotificationRuleSeverityEnum.Warning}>
                ${gettext("Warning")}
            </option>
            <option value=${NotificationRuleSeverityEnum.Notice} ?selected=${this.rule?.severity === NotificationRuleSeverityEnum.Notice}>
                ${gettext("Notice")}
            </option>
        `;
    }

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${gettext("Name")}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.rule?.name)}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Group")}
                name="group">
                <select class="pf-c-form-control">
                    <option value="" ?selected=${this.rule?.group === undefined}>---------</option>
                    ${until(new CoreApi(DEFAULT_CONFIG).coreGroupsList({}).then(groups => {
                        return groups.results.map(group => {
                            return html`<option value=${ifDefined(group.pk)} ?selected=${this.rule?.group?.groupUuid === group.pk}>${group.name}</option>`;
                        });
                    }), html``)}
                </select>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Transports")}
                ?required=${true}
                name="transports">
                <select name="users" class="pf-c-form-control" multiple>
                    ${until(new EventsApi(DEFAULT_CONFIG).eventsTransportsList({}).then(transports => {
                        return transports.results.map(transport => {
                            const selected = Array.from(this.rule?.transports || []).some(su => {
                                return su.uuid == transport.pk;
                            });
                            return html`<option value=${ifDefined(transport.pk)} ?selected=${selected}>${transport.name}</option>`;
                        });
                    }))}
                </select>
                <p class="pf-c-form__helper-text">${gettext("Select which transports should be used to notify the user. If none are selected, the notification will only be shown in the authentik UI.")}</p>
                <p class="pf-c-form__helper-text">${gettext("Hold control/command to select multiple items.")}</p>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal
                label=${gettext("Severity")}
                ?required=${true}
                name="severity">
                <select class="pf-c-form-control">
                    ${this.renderSeverity()}
                </select>
            </ak-form-element-horizontal>
        </form>`;
    }

}
