import "#components/ak-text-input";

import { DEFAULT_CONFIG } from "#common/api/config";
import { MessageLevel } from "#common/messages";

import { Form } from "#elements/forms/Form";
import { APIMessage } from "#elements/messages/Message";

import { CoreApi, User, UserBulkPanicButtonRequest } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-bulk-panic-button-form")
export class UserBulkPanicButtonForm extends Form<UserBulkPanicButtonRequest> {
    @property({ attribute: false })
    public users: User[] = [];

    protected override formatAPISuccessMessage(): APIMessage | null {
        return {
            level: MessageLevel.success,
            message: msg(str`Account lockdown triggered for ${this.users.length} user(s).`),
            description: msg("The users' accounts have been secured."),
        };
    }

    async send(data: UserBulkPanicButtonRequest): Promise<void> {
        await new CoreApi(DEFAULT_CONFIG).coreUsersPanicButtonBulkCreate({
            userBulkPanicButtonRequest: {
                ...data,
                users: this.users.map((u) => u.pk),
            },
        });
    }

    renderForm(): TemplateResult {
        return html`
            <p class="pf-c-form__helper-text" style="margin-bottom: 1rem; color: #c9190b;">
                ${msg(
                    str`This action will lock ${this.users.length} account(s), reset their passwords, and terminate all their active sessions.`,
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
            <p class="pf-c-form__helper-text" style="margin-bottom: 1rem;">
                <strong>${msg("Affected users:")}</strong>
                ${this.users.map((u) => u.username).join(", ")}
            </p>
            <ak-text-input
                name="reason"
                label=${msg("Reason")}
                autocomplete="off"
                placeholder=${msg("Reason for triggering the account lockdown")}
                help=${msg(
                    "A required explanation for locking down these accounts. This will be included in audit logs.",
                )}
                required
            ></ak-text-input>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-bulk-panic-button-form": UserBulkPanicButtonForm;
    }
}
