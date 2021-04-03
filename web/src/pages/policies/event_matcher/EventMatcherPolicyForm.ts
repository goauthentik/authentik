import { AdminApi, EventMatcherPolicy, EventsApi, PoliciesApi } from "authentik-api";
import { t } from "@lingui/macro";
import { customElement, property } from "lit-element";
import { html, TemplateResult } from "lit-html";
import { DEFAULT_CONFIG } from "../../../api/Config";
import { Form } from "../../../elements/forms/Form";
import { ifDefined } from "lit-html/directives/if-defined";
import "../../../elements/forms/HorizontalFormElement";
import "../../../elements/forms/FormGroup";
import { until } from "lit-html/directives/until";

@customElement("ak-policy-event-matcher-form")
export class EventMatcherPolicyForm extends Form<EventMatcherPolicy> {

    set policyUUID(value: string) {
        new PoliciesApi(DEFAULT_CONFIG).policiesEventMatcherRead({
            policyUuid: value,
        }).then(policy => {
            this.policy = policy;
        });
    }

    @property({attribute: false})
    policy?: EventMatcherPolicy;

    getSuccessMessage(): string {
        if (this.policy) {
            return t`Successfully updated policy.`;
        } else {
            return t`Successfully created policy.`;
        }
    }

    send = (data: EventMatcherPolicy): Promise<EventMatcherPolicy> => {
        if (this.policy) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesEventMatcherUpdate({
                policyUuid: this.policy.pk || "",
                data: data
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesEventMatcherCreate({
                data: data
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <ak-form-element-horizontal
                label=${t`Name`}
                ?required=${true}
                name="name">
                <input type="text" value="${ifDefined(this.policy?.name || "")}" class="pf-c-form-control" required>
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="executionLogging">
                <div class="pf-c-check">
                    <input type="checkbox" class="pf-c-check__input" ?checked=${this.policy?.executionLogging || false}>
                    <label class="pf-c-check__label">
                        ${t`Execution logging`}
                    </label>
                </div>
                <p class="pf-c-form__helper-text">${t`When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.`}</p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header">
                    ${t`Policy-specific settings`}
                </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal
                        label=${t`Action`}
                        name="action">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.policy?.action === undefined}>---------</option>
                            ${until(new EventsApi(DEFAULT_CONFIG).eventsEventsActions().then(actions => {
                                return actions.map(action => {
                                    return html`<option value=${action.component} ?selected=${this.policy?.action === action.component}>${action.name}</option>`;
                                });
                            }))}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Match created events with this action type. When left empty, all action types will be matched.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`Client IP`}
                        name="clientIp">
                        <input type="text" value="${ifDefined(this.policy?.clientIp || "")}" class="pf-c-form-control">
                        <p class="pf-c-form__helper-text">${t`Matches Event's Client IP (strict matching, for network matching use an Expression Policy.`}</p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal
                        label=${t`App`}
                        name="app">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.policy?.app === undefined}>---------</option>
                            ${until(new AdminApi(DEFAULT_CONFIG).adminAppsList().then(apps => {
                                return apps.map(app => {
                                    return html`<option value=${app.name} ?selected=${this.policy?.app === app.name}>${app.label}</option>`;
                                });
                            }))}
                        </select>
                        <p class="pf-c-form__helper-text">${t`Match events created by selected application. When left empty, all applications are matched.`}</p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }

}
