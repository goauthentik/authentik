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
        const response = await this.coreApi.coreUsersAccountLockdownCreate({
            userAccountLockdownRequest: {
                ...data,
                user: this.instancePk,
            },
        });
        // Redirect to the lockdown flow if one is configured
        if (response.flowUrl) {
            window.location.assign(response.flowUrl);
        }
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-account-lockdown-form": UserAccountLockdownForm;
    }
}
