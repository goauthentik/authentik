import { aki } from "#common/api/client";
import { formatDisambiguatedUserDisplayName } from "#common/users";

import { modalInvoker } from "#elements/dialogs";
import { DestructiveModelForm } from "#elements/forms/DestructiveModelForm";
import { SlottedTemplateResult } from "#elements/types";

import { CoreApi, User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

@customElement("ak-user-password-login-lock-toggle-form")
export class UserPasswordLoginLockToggleForm extends DestructiveModelForm<User> {
    protected coreAPI = aki(CoreApi);

    protected override loadInstance(): Promise<User | null> {
        return Promise.resolve(this.instance);
    }

    protected override send(): Promise<unknown> {
        if (!this.instance) {
            return Promise.reject(new Error("No user instance provided"));
        }
        return this.instance.passwordLoginLockedAt
            ? this.coreAPI.coreUsersPasswordLoginUnlockCreate({ id: this.instance.pk })
            : this.coreAPI.coreUsersPasswordLoginLockCreate({ id: this.instance.pk });
    }

    public override formatSubmitLabel(): string {
        return this.instance?.passwordLoginLockedAt
            ? msg("Unlock password login", { id: "user.action.passwordLoginUnlock" })
            : msg("Lock password login", { id: "user.action.passwordLoginLock" });
    }

    public override formatSubmittingLabel(): string {
        return this.instance?.passwordLoginLockedAt
            ? msg("Unlocking password login...", {
                  id: "user.action.passwordLoginUnlocking",
              })
            : msg("Locking password login...", { id: "user.action.passwordLoginLocking" });
    }

    protected override formatHeadline(): string {
        return this.instance?.passwordLoginLockedAt
            ? msg("Review password login unlock", {
                  id: "user.action.passwordLoginUnlockReview",
              })
            : msg("Review password login lock", { id: "user.action.passwordLoginLockReview" });
    }

    protected override renderForm(): SlottedTemplateResult {
        const displayName = formatDisambiguatedUserDisplayName(this.instance);
        return this.instance?.passwordLoginLockedAt
            ? html`<p>
                  ${msg(str`Allow ${displayName} to authenticate with a password again?`, {
                      id: "user.action.passwordLoginUnlockConfirm",
                  })}
              </p>`
            : html`<p>
                  ${msg(
                      str`Prevent ${displayName} from authenticating with a password? Existing sessions and other authentication methods are not affected.`,
                      { id: "user.action.passwordLoginLockConfirm" },
                  )}
              </p>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-password-login-lock-toggle-form": UserPasswordLoginLockToggleForm;
    }
}

export interface ToggleUserPasswordLoginLockButtonProps {
    className?: string;
}

export function ToggleUserPasswordLoginLockButton(
    user: User,
    { className = "" }: ToggleUserPasswordLoginLockButtonProps = {},
): SlottedTemplateResult {
    const locked = user.passwordLoginLockedAt !== null;
    const label = locked
        ? msg("Unlock password login", { id: "user.action.passwordLoginUnlock" })
        : msg("Lock password login", { id: "user.action.passwordLoginLock" });
    return html`<button
        class="pf-c-button pf-m-warning ${className}"
        type="button"
        ${modalInvoker(UserPasswordLoginLockToggleForm, { instance: user })}
    >
        ${label}
    </button>`;
}
