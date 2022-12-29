import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/SearchSelect";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";

import { t } from "@lingui/macro";

import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";
import { until } from "lit/directives/until.js";

import { AdminApi, EventMatcherPolicy, EventsApi, PoliciesApi, TypeCreate } from "@goauthentik/api";

@customElement("ak-policy-event-matcher-form")
export class EventMatcherPolicyForm extends ModelForm<EventMatcherPolicy, string> {
    loadInstance(pk: string): Promise<EventMatcherPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesEventMatcherRetrieve({
            policyUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return t`Successfully updated policy.`;
        } else {
            return t`Successfully created policy.`;
        }
    }

    send = (data: EventMatcherPolicy): Promise<EventMatcherPolicy> => {
        if (this.instance) {
            return new PoliciesApi(DEFAULT_CONFIG).policiesEventMatcherUpdate({
                policyUuid: this.instance.pk || "",
                eventMatcherPolicyRequest: data,
            });
        } else {
            return new PoliciesApi(DEFAULT_CONFIG).policiesEventMatcherCreate({
                eventMatcherPolicyRequest: data,
            });
        }
    };

    renderForm(): TemplateResult {
        return html`<form class="pf-c-form pf-m-horizontal">
            <div class="form-help-text">
                ${t`Matches an event against a set of criteria. If any of the configured values match, the policy passes.`}
            </div>
            <ak-form-element-horizontal label=${t`Name`} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="executionLogging">
                <div class="pf-c-check">
                    <input
                        type="checkbox"
                        class="pf-c-check__input"
                        ?checked=${first(this.instance?.executionLogging, false)}
                    />
                    <label class="pf-c-check__label"> ${t`Execution logging`} </label>
                </div>
                <p class="pf-c-form__helper-text">
                    ${t`When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.`}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${t`Policy-specific settings`} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${t`Action`} name="action">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<TypeCreate[]> => {
                                const items = await new EventsApi(
                                    DEFAULT_CONFIG,
                                ).eventsEventsActionsList();
                                return items.filter((item) =>
                                    query ? item.name.includes(query) : true,
                                );
                            }}
                            .renderElement=${(item: TypeCreate): string => {
                                return item.name;
                            }}
                            .value=${(item: TypeCreate | undefined): string | undefined => {
                                return item?.component;
                            }}
                            .selected=${(item: TypeCreate): boolean => {
                                return this.instance?.action === item.component;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${t`Match created events with this action type. When left empty, all action types will be matched.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`Client IP`} name="clientIp">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.clientIp || "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${t`Matches Event's Client IP (strict matching, for network matching use an Expression Policy.`}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${t`App`} name="app">
                        <select class="pf-c-form-control">
                            <option value="" ?selected=${this.instance?.app === undefined}>
                                ---------
                            </option>
                            ${until(
                                new AdminApi(DEFAULT_CONFIG).adminAppsList().then((apps) => {
                                    return apps.map((app) => {
                                        return html`<option
                                            value=${app.name}
                                            ?selected=${this.instance?.app === app.name}
                                        >
                                            ${app.label}
                                        </option>`;
                                    });
                                }),
                                html`<option>${t`Loading...`}</option>`,
                            )}
                        </select>
                        <p class="pf-c-form__helper-text">
                            ${t`Match events created by selected application. When left empty, all applications are matched.`}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>
        </form>`;
    }
}
