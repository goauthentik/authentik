import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";
import { APIMessage } from "#elements/messages/Message";

import { CoreApi, UserPanicButtonRequest } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-panic-button-form")
export class UserPanicButtonForm extends Form<UserPanicButtonRequest> {
    @property({ type: Number })
    public instancePk?: number;

    protected override formatAPISuccessMessage(): APIMessage | null {
        return {
            level: MessageLevel.success,
            message: msg(str`Account lockdown triggered successfully.`),
            description: msg("The user's account has been secured."),
        };
    }

    async send(data: UserPanicButtonRequest): Promise<void> {
        await new CoreApi(DEFAULT_CONFIG).coreUsersPanicButtonCreate({
            id: this.instancePk || 0,
            userPanicButtonRequest: data,
        });
    }

    renderForm(): TemplateResult {
        return html`
            <p class="pf-c-form__helper-text" style="margin-bottom: 1rem; color: #c9190b;">
                ${msg(
                    "This action will lock the account, reset the password, and terminate all active sessions.",
                )}
            </p>
            <p class="pf-c-form__helper-text" style="margin-bottom: 1rem;">
                <a
                    href="https://docs.goauthentik.io/security/account-lockdown/"
                    target="_blank"
                    rel="noopener noreferrer"
                    >${msg("Learn more about Account Lockdown")}</a
                >
            </p>
            <ak-text-input
                name="reason"
                label=${msg("Reason")}
                autocomplete="off"
                placeholder=${msg("Reason for triggering the account lockdown")}
                help=${msg(
                    "A required explanation for locking down this account. This will be included in audit logs.",
                )}
                required
            ></ak-text-input>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-panic-button-form": UserPanicButtonForm;
    }
}
