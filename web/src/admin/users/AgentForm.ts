import "#components/ak-hidden-text-input";
import "#elements/forms/HorizontalFormElement";
import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";

import { Form } from "#elements/forms/Form";
import { ModalForm } from "#elements/forms/ModalForm";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, UserAgentRequest, UserAgentResponse } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

@customElement("ak-user-agent-form")
export class AgentForm extends Form<UserAgentRequest> {
    public static override verboseName = msg("Agent");
    public static override verboseNamePlural = msg("Agents");
    public override cancelButtonLabel = msg("Close");

    @property({ attribute: false })
    result: UserAgentResponse | null = null;

    getSuccessMessage(): string {
        return msg("Successfully created agent user.");
    }

    async send(data: UserAgentRequest): Promise<UserAgentResponse> {
        const result = await new CoreApi(DEFAULT_CONFIG).coreUsersAgentCreate({
            userAgentRequest: data,
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

    protected override renderForm(): TemplateResult {
        return html`<ak-text-input
            name="name"
            label=${msg("Username")}
            placeholder=${msg("Type a username for the agent...")}
            value=""
            input-hint="code"
            required
            maxlength=${150}
            autofocus
            help=${msg(
                "The agent's primary identifier used for authentication. 150 characters or fewer.",
            )}
        ></ak-text-input>`;
    }

    protected renderResponseForm(): SlottedTemplateResult {
        return html`<p>
                ${msg(
                    "Use the username and token below to authenticate. The token expires in 24 hours and must be rotated before expiry.",
                )}
            </p>
            <form class="pf-c-form pf-m-horizontal">
                <ak-text-input
                    name="name"
                    label=${msg("Username")}
                    autocomplete="off"
                    value=${ifDefined(this.result?.username)}
                    input-hint="code"
                    readonly
                ></ak-text-input>

                <ak-hidden-text-input
                    label=${msg("Token")}
                    value="${this.result?.token ?? ""}"
                    input-hint="code"
                    readonly
                    .help=${msg(
                        "Valid for 24 hours. The agent must rotate the token before it expires. If the rotation window is missed, the owner must issue a new token.",
                    )}
                >
                </ak-hidden-text-input>
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
        "ak-user-agent-form": AgentForm;
    }
}
