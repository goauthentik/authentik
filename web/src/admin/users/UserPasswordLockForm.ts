import { aki } from "#common/api/client";
import { formatDisambiguatedUserDisplayName } from "#common/users";

import { modalInvoker } from "#elements/dialogs";
import { DestructiveModelForm } from "#elements/forms/DestructiveModelForm";
import { WithLocale } from "#elements/mixins/locale";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, User, UserTypeEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-user-password-lock-form")
export class UserPasswordLockForm extends WithLocale(DestructiveModelForm<User>) {
    protected coreAPI = aki(CoreApi);

    protected get locked(): boolean {
        return !!this.instance?.passwordLocked;
    }

    protected override send(): Promise<unknown> {
        if (!this.instance) {
            return Promise.reject(new Error("No user instance provided"));
        }
        return this.locked
            ? this.coreAPI.coreUsersUnlockPasswordCreate({ id: this.instance.pk })
            : this.coreAPI.coreUsersLockPasswordCreate({ id: this.instance.pk });
    }

    public override formatSubmitLabel(): string {
        return this.locked
            ? msg("Unlock password login", { id: "user.action.password-unlock.label" })
            : msg("Lock password login", { id: "user.action.password-lock.label" });
    }

    protected override formatHeadline(): string {
        return this.locked
            ? msg("Review password unlock", { id: "user.action.password-unlock-review.label" })
            : msg("Review password lock", { id: "user.action.password-lock-review.label" });
    }

    protected override renderForm(): SlottedTemplateResult {
        const displayName = this.instance
            ? formatDisambiguatedUserDisplayName(this.instance, this.activeLanguageTag)
            : msg("Unknown user");
        return html`<p>
            ${this.locked
                ? msg(str`Allow ${displayName} to authenticate with a password again?`, {
                      id: "user.action.password-unlock-confirm.description",
                  })
                : msg(
                      str`Prevent ${displayName} from authenticating with a password? Existing sessions and other authentication methods are not affected.`,
                      { id: "user.action.password-lock-confirm.description" },
                  )}
        </p>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-password-lock-form": UserPasswordLockForm;
    }
}

export interface ToggleUserPasswordLockButtonProps {
    className?: string;
    hasEnterpriseLicense?: boolean;
}

export function ToggleUserPasswordLockButton(
    user: User,
    { className = "", hasEnterpriseLicense = false }: ToggleUserPasswordLockButtonProps = {},
): SlottedTemplateResult {
    const locked = !!user.passwordLocked;
    const serviceAccount =
        user.type === UserTypeEnum.ServiceAccount ||
        user.type === UserTypeEnum.InternalServiceAccount;
    // Unlocking never requires a license; locking does, and service accounts
    // have no password to lock.
    if (!locked && (!hasEnterpriseLicense || serviceAccount)) {
        return nothing;
    }

    const label = locked
        ? msg("Unlock password login", { id: "user.action.password-unlock.label" })
        : msg("Lock password login", { id: "user.action.password-lock.label" });
    return html`<button
        class="pf-c-button pf-m-warning ${className}"
        type="button"
        ${modalInvoker(UserPasswordLockForm, { instance: user })}
    >
        ${label}
    </button>`;
}
