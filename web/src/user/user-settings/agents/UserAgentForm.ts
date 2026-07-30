import "#elements/forms/HorizontalFormElement";
import "#components/ak-text-input";
import "#components/ak-switch-input";

import { aki } from "#common/api/client";
import { dateTimeLocal } from "#common/temporal";

import { Form } from "#elements/forms/Form";
import { SlottedTemplateResult } from "#elements/types";

import { AKLabel } from "#components/ak-label";

import { Agent, AgentCreateRequest, AgentsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, state } from "lit/decorators.js";

@customElement("ak-user-agent-form")
export class UserAgentForm extends Form<AgentCreateRequest> {
    public static override verboseName = msg("Agent");
    public static override verboseNamePlural = msg("Agents");
    public static override createLabel = msg("Create");
    public static override submitVerb = msg("Create");

    @state()
    protected expiresAt: Date | null = null;

    getSuccessMessage(): string {
        return msg("Successfully created agent.");
    }

    async send(data: AgentCreateRequest): Promise<Agent> {
        // Self-service creation: `parent` is omitted, so the server owns the agent to
        // the requesting user.
        return aki(AgentsApi).agentsAgentsCreate({
            agentCreateRequest: data,
        });
    }

    #expiringChangeListener = (event: Event) => {
        const expiringElement = event.target as HTMLInputElement;
        this.expiresAt = expiringElement.checked ? new Date() : null;
    };

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-text-input
                name="label"
                label=${msg("Label")}
                value=""
                help=${msg("Optional display name for this agent.")}
            ></ak-text-input>

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
                        htmlFor: "user-agent-expiration-date-input",
                    },
                    msg("Expires on"),
                )}

                <input
                    id="user-agent-expiration-date-input"
                    type="datetime-local"
                    data-type="datetime-local"
                    value=${this.expiresAt ? dateTimeLocal(this.expiresAt) : ""}
                    ?disabled=${!this.expiresAt}
                    class="pf-c-form-control"
                />
            </ak-form-element-horizontal>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-agent-form": UserAgentForm;
    }
}
