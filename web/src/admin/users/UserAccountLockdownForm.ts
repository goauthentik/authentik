import { AccountLockdownRequest, SingleUserAccountLockdownForm } from "./AccountLockdownFormBase";

import { customElement, property } from "lit/decorators.js";

/**
 * Admin form for triggering account lockdown on a specific user.
 */
@customElement("ak-user-account-lockdown-form")
export class UserAccountLockdownForm extends SingleUserAccountLockdownForm {
    @property({ type: Number })
    public instancePk?: number;

    async send(data: AccountLockdownRequest): Promise<void> {
        await this.coreApi.coreUsersAccountLockdownCreate({
            id: this.instancePk || 0,
            userAccountLockdownRequest: data,
        });
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-account-lockdown-form": UserAccountLockdownForm;
    }
}
