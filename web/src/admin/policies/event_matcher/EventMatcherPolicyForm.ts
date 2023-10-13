import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import { first } from "@goauthentik/common/utils";
import "@goauthentik/elements/forms/FormGroup";
import "@goauthentik/elements/forms/HorizontalFormElement";
import { ModelForm } from "@goauthentik/elements/forms/ModelForm";
import "@goauthentik/elements/forms/SearchSelect";

import { msg } from "@lit/localize";
import { TemplateResult, html } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import {
    AdminApi,
    App,
    EventMatcherPolicy,
    EventsApi,
    PoliciesApi,
    TypeCreate,
} from "@goauthentik/api";

@customElement("ak-policy-event-matcher-form")
export class EventMatcherPolicyForm extends ModelForm<EventMatcherPolicy, string> {
    loadInstance(pk: string): Promise<EventMatcherPolicy> {
        return new PoliciesApi(DEFAULT_CONFIG).policiesEventMatcherRetrieve({
            policyUuid: pk,
        });
    }

    getSuccessMessage(): string {
        if (this.instance) {
            return msg("Successfully updated policy.");
        } else {
            return msg("Successfully created policy.");
        }
    }

    async send(data: EventMatcherPolicy): Promise<EventMatcherPolicy> {
        if (data.action?.toString() === "") data.action = null;
        if (data.clientIp?.toString() === "") data.clientIp = null;
        if (data.app?.toString() === "") data.app = null;
        if (data.model?.toString() === "") data.model = null;
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
    }

    renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Matches an event against a set of criteria. If any of the configured values match, the policy passes.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} ?required=${true} name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-form-element-horizontal name="executionLogging">
                <label class="pf-c-switch">
                    <input
                        class="pf-c-switch__input"
                        type="checkbox"
                        ?checked=${first(this.instance?.executionLogging, false)}
                    />
                    <span class="pf-c-switch__toggle">
                        <span class="pf-c-switch__toggle-icon">
                            <i class="fas fa-check" aria-hidden="true"></i>
                        </span>
                    </span>
                    <span class="pf-c-switch__label">${msg("Execution logging")}</span>
                </label>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.",
                    )}
                </p>
            </ak-form-element-horizontal>
            <ak-form-group .expanded=${true}>
                <span slot="header"> ${msg("Policy-specific settings")} </span>
                <div slot="body" class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Action")} name="action">
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
                            ${msg(
                                "Match created events with this action type. When left empty, all action types will be matched.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Client IP")} name="clientIp">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.clientIp || "")}"
                            class="pf-c-form-control"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Matches Event's Client IP (strict matching, for network matching use an Expression Policy.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("App")} name="app">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<App[]> => {
                                const items = await new AdminApi(DEFAULT_CONFIG).adminAppsList();
                                return items.filter((item) =>
                                    query ? item.name.includes(query) : true,
                                );
                            }}
                            .renderElement=${(item: App): string => {
                                return item.label;
                            }}
                            .value=${(item: App | undefined): string | undefined => {
                                return item?.name;
                            }}
                            .selected=${(item: App): boolean => {
                                return this.instance?.app === item.name;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Match events created by selected application. When left empty, all applications are matched.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Model")} name="model">
                        <ak-search-select
                            .fetchObjects=${async (query?: string): Promise<App[]> => {
                                const items = await new AdminApi(DEFAULT_CONFIG).adminModelsList();
                                return items
                                    .filter((item) => (query ? item.name.includes(query) : true))
                                    .sort((a, b) => {
                                        if (a.name < b.name) return -1;
                                        if (a.name > b.name) return 1;
                                        return 0;
                                    });
                            }}
                            .renderElement=${(item: App): string => {
                                return `${item.label} (${item.name.split(".")[0]})`;
                            }}
                            .value=${(item: App | undefined): string | undefined => {
                                return item?.name;
                            }}
                            .selected=${(item: App): boolean => {
                                return this.instance?.model === item.name;
                            }}
                            ?blankable=${true}
                        >
                        </ak-search-select>
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Match events created by selected model. When left empty, all models are matched.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                </div>
            </ak-form-group>`;
    }
}
