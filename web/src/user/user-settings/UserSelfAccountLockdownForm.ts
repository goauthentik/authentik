import "#components/ak-switch-input";

import {
    AccountLockdownRequest,
    SingleUserAccountLockdownForm,
} from "#admin/users/AccountLockdownFormBase";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, state } from "lit/decorators.js";

/**
 * Self-service account lockdown form for users to lock their own account.
 */
@customElement("ak-user-self-account-lockdown-form")
export class UserSelfAccountLockdownForm extends SingleUserAccountLockdownForm {
    @state()
    private confirmed = false;

    // Override messages for first-person context
    protected override get warningTitle(): string {
        return msg("You are about to lock your account");
    }

    protected override get infoMessage(): string {
        return msg("Use this if you suspect your account has been compromised.");
    }

    protected override get reasonPlaceholder(): string {
        return msg("Describe why you are locking your account...");
    }

    protected override get successDescription(): string {
        return msg("Your account has been secured. You will be logged out.");
    }

    protected override get affectedUserLabel(): string {
        return msg("Account");
    }

    protected override get usernameDisplay(): string | TemplateResult {
        return html`${this.username} (${msg("your account")})`;
    }

    /**
     * Renders a confirmation checkbox that must be checked before submitting.
     */
    protected renderConfirmationCheckbox(): TemplateResult {
        return html`
            <ak-switch-input
                name="confirm"
                label=${msg("I understand this action cannot be undone")}
                help=${msg(
                    "Check this box to confirm you want to lock your account. You will need to contact an administrator to restore access.",
                )}
                @change=${(e: Event) => {
                    this.confirmed = (e.target as HTMLInputElement).checked;
                }}
                required
            ></ak-switch-input>
        `;
    }

    override renderForm(): TemplateResult {
        return html`
            ${this.renderWarningAlert()} ${this.renderInfoAlert()} ${this.renderAffectedUsers()}
            ${this.renderReasonInput()} ${this.renderConfirmationCheckbox()}
        `;
    }

    async send(data: AccountLockdownRequest): Promise<void> {
        if (!this.confirmed) {
            throw new Error(
                msg("You must confirm that you understand this action cannot be undone."),
            );
        }
        await this.coreApi.coreUsersAccountLockdownSelfCreate({
            userAccountLockdownRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-self-account-lockdown-form": UserSelfAccountLockdownForm;
    }
}
