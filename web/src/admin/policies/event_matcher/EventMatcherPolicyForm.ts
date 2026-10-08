import "#components/ak-switch-input";
import "#elements/forms/FormGroup";
import "#elements/forms/HorizontalFormElement";
import { aki } from "#common/api/client";
import { docLink } from "#common/global";

import { SearchSelectSource } from "#elements/forms/SearchSelect/shared";

import { AKSearchSelect } from "#components/ak-search-select-field";

import { BasePolicyForm } from "#admin/policies/BasePolicyForm";

import {
    AdminApi,
    App,
    EventMatcherPolicy,
    EventsApi,
    PoliciesApi,
    TypeCreate,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const eventActionSource: SearchSelectSource<TypeCreate> = {
    fetchObjects: async (query) => {
        const actions = await aki(EventsApi).eventsEventsActionsList();

        return actions.filter((action) =>
            query ? action.name.toLowerCase().includes(query.toLowerCase()) : true,
        );
    },
    keyOf: (action) => action.component,
    labelOf: (action) => action.name,
};

const appSource: SearchSelectSource<App> = {
    fetchObjects: async (query) => {
        const apps = await aki(AdminApi).adminAppsList();

        return apps.filter((app) => (query ? app.name.includes(query) : true));
    },
    keyOf: (app) => app.name,
    labelOf: (app) => app.label,
};

const modelSource: SearchSelectSource<App> = {
    fetchObjects: async (query) => {
        const models = await aki(AdminApi).adminModelsList();

        return models
            .filter((model) => (query ? model.name.includes(query) : true))
            .sort((a, b) => a.name.localeCompare(b.name));
    },
    keyOf: (model) => model.name,
    labelOf: (model) => `${model.label} (${model.name.split(".")[0]})`,
};

@customElement("ak-policy-event-matcher-form")
export class EventMatcherPolicyForm extends BasePolicyForm<EventMatcherPolicy> {
    override loadInstance(pk: string): Promise<EventMatcherPolicy> {
        return aki(PoliciesApi).policiesEventMatcherRetrieve({
            policyUuid: pk,
        });
    }

    async send(data: EventMatcherPolicy): Promise<EventMatcherPolicy> {
        if (data.query?.toString() === "") data.query = null;

        if (data.action?.toString() === "") data.action = null;

        if (data.clientIp?.toString() === "") data.clientIp = null;

        if (data.app?.toString() === "") data.app = null;

        if (data.model?.toString() === "") data.model = null;

        if (this.instance) {
            return aki(PoliciesApi).policiesEventMatcherUpdate({
                policyUuid: this.instance.pk || "",
                eventMatcherPolicyRequest: data,
            });
        }

        return aki(PoliciesApi).policiesEventMatcherCreate({
            eventMatcherPolicyRequest: data,
        });
    }

    protected override renderForm(): TemplateResult {
        return html` <span>
                ${msg(
                    "Matches an event against a set of criteria. If any of the configured values match, the policy passes.",
                )}
            </span>
            <ak-form-element-horizontal label=${msg("Name")} required name="name">
                <input
                    type="text"
                    value="${ifDefined(this.instance?.name || "")}"
                    class="pf-c-form-control"
                    required
                />
            </ak-form-element-horizontal>
            <ak-switch-input
                name="executionLogging"
                label=${msg("Execution logging")}
                ?checked=${this.instance?.executionLogging ?? false}
                help=${msg(
                    "When this option is enabled, all executions of this policy will be logged. By default, only execution errors are logged.",
                )}
            >
            </ak-switch-input>
            <ak-form-group open label="${msg("Policy-specific settings")}">
                <div class="pf-c-form">
                    <ak-form-element-horizontal label=${msg("Query")} name="query">
                        <input
                            type="text"
                            value="${ifDefined(this.instance?.query || "")}"
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg("Event query using the AKQL syntax.")}
                            <a
                                rel="noopener noreferrer"
                                target="_blank"
                                href=${docLink(
                                    "/sys-mgmt/akql/#use-akql-in-an-event-matcher-policy",
                                )}
                            >
                                ${msg("See documentation for examples.")}
                            </a>
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Action")} name="action">
                        ${AKSearchSelect({
                            name: "action",
                            source: eventActionSource,
                            value: this.instance?.action,
                            blankable: true,
                        })}
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
                            class="pf-c-form-control pf-m-monospace"
                            autocomplete="off"
                            spellcheck="false"
                        />
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Matches Event's Client IP (strict matching, for network matching use an Expression Policy).",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("App")} name="app">
                        ${AKSearchSelect({
                            name: "app",
                            source: appSource,
                            value: this.instance?.app,
                            blankable: true,
                        })}
                        <p class="pf-c-form__helper-text">
                            ${msg(
                                "Match events created by selected application. When left empty, all applications are matched.",
                            )}
                        </p>
                    </ak-form-element-horizontal>
                    <ak-form-element-horizontal label=${msg("Model")} name="model">
                        ${AKSearchSelect({
                            name: "model",
                            source: modelSource,
                            value: this.instance?.model,
                            blankable: true,
                        })}
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-policy-event-matcher-form": EventMatcherPolicyForm;
    }
}
