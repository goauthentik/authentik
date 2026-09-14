import "#components/ak-hidden-text-input";
import "#components/ak-text-input";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { Form } from "#elements/forms/Form";
import { ModalForm } from "#elements/forms/ModalForm";
import { SlottedTemplateResult } from "#elements/types";

import { AgentCreated, AgentCreateRequest, AgentsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-user-agent-form")
export class UserAgentForm extends Form<AgentCreateRequest> {
    public static override verboseName = msg("Agent", { id: "agent.verbose-name.label" });
    public static override verboseNamePlural = msg("Agents", {
        id: "agent.verbose-name-plural.label",
    });
    public static override createLabel = msg("Create", { id: "agent.create.label" });
    public static override submitVerb = msg("Create", { id: "agent.create.submit" });
    public override cancelButtonLabel = msg("Close", { id: "agent.form.close.label" });

    @property({ attribute: false })
    public result: AgentCreated | null = null;

    getSuccessMessage(): string {
        return msg("Successfully created agent.", { id: "agent.create.success" });
    }

    async send(data: AgentCreateRequest): Promise<AgentCreated> {
        // Self-service creation: `parent` and expiry are set by the server (owned by the
        // requesting user, always expiring).
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

    protected override renderForm(): SlottedTemplateResult {
        return html`<ak-text-input
                name="label"
                label=${msg("Label", { id: "agent.label.label" })}
                value=""
                help=${msg("Optional display name for this agent.", {
                    id: "agent.label.description",
                })}
            ></ak-text-input>
            <p class="pf-c-form__helper-text">
                ${msg(
                    "This agent mirrors your access: it can act on exactly the applications you can, and never more.",
                    { id: "agent.mirror.description" },
                )}
            </p>`;
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
        "ak-user-agent-form": UserAgentForm;
    }
}
