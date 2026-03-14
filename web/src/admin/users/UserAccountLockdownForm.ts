import "#elements/forms/HorizontalFormElement";

import { AccountLockdownFormBase, AccountLockdownRequest } from "./AccountLockdownFormBase";

import { MessageLevel } from "#common/messages";

import { APIMessage } from "#elements/messages/Message";

import { msg, str } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

@customElement("ak-user-account-lockdown-form")
export class UserAccountLockdownForm extends AccountLockdownFormBase<AccountLockdownRequest> {
    @property({ type: Number })
    public instancePk?: number;

    @property({ type: String })
    public username?: string;

    protected override formatAPISuccessMessage(): APIMessage | null {
        return {
            level: MessageLevel.success,
            message: msg(str`Account lockdown triggered successfully.`),
            description: msg("The user's account has been secured."),
        };
    }

    async send(data: AccountLockdownRequest): Promise<void> {
        await this.coreApi.coreUsersAccountLockdownCreate({
            id: this.instancePk || 0,
            userAccountLockdownRequest: data,
        });
    }

    protected renderAffectedUsers(): TemplateResult {
        if (!this.username) {
            return html`${nothing}`;
        }
        return html`
            <ak-form-element-horizontal label=${msg("Affected user")}>
                <div class="pf-c-form-control-static">${this.username}</div>
            </ak-form-element-horizontal>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-account-lockdown-form": UserAccountLockdownForm;
    }
}
