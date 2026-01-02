import "#elements/forms/HorizontalFormElement";

import { MessageLevel } from "#common/messages";

import { APIMessage } from "#elements/messages/Message";

import {
    AccountLockdownFormBase,
    AccountLockdownRequest,
} from "#admin/users/AccountLockdownFormBase";

import { msg, str } from "@lit/localize";
import { html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-self-account-lockdown-form")
export class UserSelfAccountLockdownForm extends AccountLockdownFormBase<AccountLockdownRequest> {
    @property({ type: String })
    public username?: string;

    protected override get warningTitle(): string {
        return msg("You are about to lock your account");
    }

    protected override get infoMessage(): string {
        return msg("Use this if you suspect your account has been compromised.");
    }

    protected override get reasonPlaceholder(): string {
        return msg("Describe why you are locking your account...");
    }

    protected override formatAPISuccessMessage(): APIMessage | null {
        return {
            level: MessageLevel.success,
            message: msg(str`Account lockdown triggered successfully.`),
            description: msg("Your account has been secured. You will be logged out."),
        };
    }

    async send(data: AccountLockdownRequest): Promise<void> {
        await this.coreApi.coreUsersAccountLockdownSelfCreate({
            userAccountLockdownRequest: data,
        });
    }

    protected renderAffectedUsers(): TemplateResult {
        return html`
            <ak-form-element-horizontal label=${msg("Account")}>
                <div class="pf-c-form-control-static">
                    ${this.username} (${msg("your account")})
                </div>
            </ak-form-element-horizontal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-self-account-lockdown-form": UserSelfAccountLockdownForm;
    }
}
