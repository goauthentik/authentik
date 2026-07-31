import "#components/ak-hidden-text-input";
import "#components/ak-text-input";
import "#elements/ak-dual-select/ak-dual-select-provider";
import "#elements/forms/HorizontalFormElement";

import { aki } from "#common/api/client";

import { DataProvider, DualSelectPair } from "#elements/ak-dual-select/types";
import { Form } from "#elements/forms/Form";
import { ModalForm } from "#elements/forms/ModalForm";
import { SlottedTemplateResult } from "#elements/types";

import {
    AgentCreated,
    AgentCreateRequest,
    AgentsApi,
    Application,
    CoreApi,
} from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

const applicationPair = (app: Application): DualSelectPair => [
    app.pk,
    html`<div class="selection-main">${app.name}</div>
        <div class="selection-desc">${app.slug}</div>`,
    app.name,
];

// coreApplicationsList is already scoped to the applications the requesting user can access,
// so a self-service user can only scope their agent to apps they themselves can reach.
const applicationProvider: DataProvider = async (page, search = "") => {
    const apps = await aki(CoreApi).coreApplicationsList({
        page,
        search,
        ordering: "name",
    });
    return {
        pagination: apps.pagination,
        options: apps.results.map(applicationPair),
    };
};

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
                        "The agent can act only on these applications, and never on more than you can access yourself.",
                        { id: "agent.applications.description" },
                    )}
                </p>
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
        "ak-user-agent-form": UserAgentForm;
    }
}
