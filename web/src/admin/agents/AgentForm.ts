import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#elements/ak-dual-select/ak-dual-select-provider";
import "#components/ak-text-input";
import "#components/ak-switch-input";
import "#components/ak-hidden-text-input";

import { aki } from "#common/api/client";
import { dateTimeLocal } from "#common/temporal";

import { DataProvider, DualSelectPair } from "#elements/ak-dual-select/types";
import { Form } from "#elements/forms/Form";
import { ModalForm } from "#elements/forms/ModalForm";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import {
    AgentCreated,
    AgentCreateRequest,
    AgentsApi,
    Application,
    CoreApi,
    CoreUsersListRequest,
    User,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const applicationPair = (app: Application): DualSelectPair => [
    app.pk,
    html`<div class="selection-main">${app.name}</div>
        <div class="selection-desc">${app.slug}</div>`,
    app.name,
];

const applicationProvider: DataProvider = async (page, search = "") => {
    const apps = await aki(CoreApi).coreApplicationsList({ page, search, ordering: "name" });
    return {
        pagination: apps.pagination,
        options: apps.results.map(applicationPair),
    };
};

@customElement("ak-agent-form")
export class AgentForm extends Form<AgentCreateRequest> {
    public static override verboseName = msg("Agent");
    public static override verboseNamePlural = msg("Agents");
    public static override createLabel = msg("Create");
    public static override submitVerb = msg("Create");
    public override cancelButtonLabel = msg("Close", { id: "agent.form.close.label" });

    @state()
    protected expiresAt: Date | null = null;

    @property({ attribute: false })
    public result: AgentCreated | null = null;

    getSuccessMessage(): string {
        return msg("Successfully created agent.");
    }

    async send(data: AgentCreateRequest): Promise<AgentCreated> {
        const result = await aki(AgentsApi).agentsAgentsCreate({
            agentCreateRequest: data,
        });
        this.result = result;
        if (this.parentElement instanceof ModalForm) {
            this.parentElement.showSubmitButton = false;
        }
        return result;
    }

    public override reset(): void {
        super.reset();
        this.result = null;
        if (this.parentElement instanceof ModalForm) {
            this.parentElement.showSubmitButton = true;
        }
    }

    #expiringChangeListener = (event: Event) => {
        const expiringElement = event.target as HTMLInputElement;
        this.expiresAt = expiringElement.checked ? new Date() : null;
    };

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-form-element-horizontal label=${msg("Parent user")} name="parent" required>
                <ak-search-select
                    .fetchObjects=${async (query?: string): Promise<User[]> => {
                        const args: CoreUsersListRequest = {
                            ordering: "username",
                        };
                        if (query !== undefined) {
                            args.search = query;
                        }
                        const users = await aki(CoreApi).coreUsersList(args);
                        return users.results;
                    }}
                    .renderElement=${(user: User) => user.username}
                    .renderDescription=${(user: User) => html`${user.name}`}
                    .value=${(user: User | null) => user?.pk}
                >
                </ak-search-select>
                <p class="pf-c-form__helper-text">
                    ${msg("The user this agent acts on behalf of.")}
                </p>
            </ak-form-element-horizontal>

            <ak-text-input
                name="label"
                label=${msg("Label")}
                value=""
                help=${msg("Optional display name. Defaults to the parent user's name.")}
            ></ak-text-input>

            <ak-form-element-horizontal
                label=${msg("Applications", { id: "agent.applications.label" })}
                name="applications"
            >
                <ak-dual-select-provider
                    .provider=${applicationProvider}
                    .selected=${[]}
                    available-label=${msg("Available applications", {
                        id: "agent.applications.available",
                    })}
                    selected-label=${msg("Selected applications", {
                        id: "agent.applications.selected",
                    })}
                ></ak-dual-select-provider>
                <p class="pf-c-form__helper-text">
                    ${msg(
                        "The agent can act only on these applications, and never on more than its owner can access.",
                        { id: "agent.applications.description-admin" },
                    )}
                </p>
            </ak-form-element-horizontal>

            <ak-switch-input
                name="expiring"
                label=${msg("Expiring")}
                help=${msg("Whether this agent should be automatically removed once it expires.")}
                @change=${this.#expiringChangeListener}
                ?checked=${!!this.expiresAt}
            ></ak-switch-input>

            <ak-form-element-horizontal name="expires">
                ${AKLabel(
                    {
                        slot: "label",
                        className: "pf-c-form__group-label",
                        htmlFor: "agent-expiration-date-input",
                    },
                    msg("Expires on"),
                )}

                <input
                    id="agent-expiration-date-input"
                    type="datetime-local"
                    data-type="datetime-local"
                    value=${this.expiresAt ? dateTimeLocal(this.expiresAt) : ""}
                    ?disabled=${!this.expiresAt}
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>`;
    }

    protected renderResponseForm(): SlottedTemplateResult {
        return html`<p>
                ${msg(
                    "Use the token below to authenticate as this agent. It is shown only once — store it now.",
                    { id: "agent.token.description" },
                )}
            </p>
            <form class="pf-c-form pf-m-horizontal">
                <ak-hidden-text-input
                    label=${msg("Token", { id: "agent.token.label" })}
                    value=${ifDefined(this.result?.token)}
                    input-hint="code"
                    readonly
                ></ak-hidden-text-input>
            </form>`;
    }

    protected override renderFormWrapper(): SlottedTemplateResult {
        if (this.result) {
            return this.renderResponseForm();
        }
        return super.renderFormWrapper();
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-agent-form": AgentForm;
    }
}
