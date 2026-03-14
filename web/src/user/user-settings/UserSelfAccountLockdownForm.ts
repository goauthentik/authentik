import {
    AccountLockdownRequest,
    SingleUserAccountLockdownForm,
} from "#admin/users/AccountLockdownFormBase";

import { msg } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement } from "lit/decorators.js";

/**
 * Self-service account lockdown form for users to lock their own account.
 */
@customElement("ak-user-self-account-lockdown-form")
export class UserSelfAccountLockdownForm extends SingleUserAccountLockdownForm {
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

    async send(data: AccountLockdownRequest): Promise<void> {
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
