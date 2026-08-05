import "#elements/forms/HorizontalFormElement";
import "#elements/forms/SearchSelect/index";
import "#components/ak-text-input";
import "#components/ak-switch-input";
import "#components/ak-radio-input";
import "#components/ak-hidden-text-input";

import { aki } from "#common/api/client";
import { dateTimeLocal } from "#common/temporal";

import { Form } from "#elements/forms/Form";
import { ModalForm } from "#elements/forms/ModalForm";
import { RadioOption } from "#elements/forms/Radio";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import {
    AgentCreated,
    AgentCreateRequest,
    AgentsApi,
    CoreApi,
    CoreUsersListRequest,
    PolicyBehaviorEnum,
    User,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property, state } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

function createPolicyBehaviorOptions(): RadioOption<PolicyBehaviorEnum>[] {
    return [
        {
            label: msg("Mirror", { id: "agent.policy-behavior.mirror.label" }),
            value: PolicyBehaviorEnum.Mirror,
            default: true,
            description: msg("The agent has exactly the parent user's access, evaluated live.", {
                id: "agent.policy-behavior.mirror.description",
            }),
        },
        {
            label: msg("Copy", { id: "agent.policy-behavior.copy.label" }),
            value: PolicyBehaviorEnum.Copy,
            description: msg("Copy the parent's policy bindings onto the agent.", {
                id: "agent.policy-behavior.copy.description",
            }),
        },
        {
            label: msg("None", { id: "agent.policy-behavior.none.label" }),
            value: PolicyBehaviorEnum.None,
            description: msg("The agent uses only its own policy bindings.", {
                id: "agent.policy-behavior.none.description",
            }),
        },
    ];
}

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

    protected override async send(data: AgentCreateRequest): Promise<AgentCreated> {
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

            <ak-radio-input
                name="policyBehavior"
                label=${msg("Policy behavior", { id: "agent.policy-behavior.label" })}
                .options=${createPolicyBehaviorOptions}
                help=${msg("How the agent's access relates to its parent user.", {
                    id: "agent.policy-behavior.help",
                })}
            ></ak-radio-input>

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
                    copyable
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
