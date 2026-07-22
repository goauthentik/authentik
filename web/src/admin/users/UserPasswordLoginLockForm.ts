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

    protected get isLocked(): boolean {
        return Boolean(this.instance?.passwordLoginLockedAt);
    }

    protected override send(): Promise<unknown> {
        if (!this.instance) {
            return Promise.reject(new Error("No user instance provided"));
        }
        return this.isLocked
            ? this.coreAPI.coreUsersPasswordLoginUnlockCreate({ id: this.instance.pk })
            : this.coreAPI.coreUsersPasswordLoginLockCreate({ id: this.instance.pk });
    }

    public override formatSubmitLabel(): string {
        return this.isLocked
            ? msg("Unlock password login", { id: "user.action.password-login-unlock" })
            : msg("Lock password login", { id: "user.action.password-login-lock" });
    }

    public override formatSubmittingLabel(): string {
        return this.isLocked
            ? msg("Unlocking password login...", {
                  id: "user.action.password-login-unlocking",
              })
            : msg("Locking password login...", { id: "user.action.password-login-locking" });
    }

    protected override formatHeadline(): string {
        return this.isLocked
            ? msg("Review password login unlock", {
                  id: "user.action.password-login-unlock-review",
              })
            : msg("Review password login lock", {
                  id: "user.action.password-login-lock-review",
              });
    }

    protected override renderForm(): SlottedTemplateResult {
        const displayName = formatDisambiguatedUserDisplayName(this.instance);
        return this.isLocked
            ? html`<p>
                  ${msg(str`Allow ${displayName} to authenticate with a password again?`, {
                      id: "user.action.password-login-unlock-confirm",
                  })}
              </p>`
            : html`<p>
                  ${msg(
                      str`Prevent ${displayName} from authenticating with a password? Existing sessions and other authentication methods are not affected.`,
                      { id: "user.action.password-login-lock-confirm" },
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
    const locked = Boolean(user.passwordLoginLockedAt);
    const label = locked
        ? msg("Unlock password login", { id: "user.action.password-login-unlock" })
        : msg("Lock password login", { id: "user.action.password-login-lock" });
    return html`<button
        class="pf-c-button pf-m-warning ${className}"
        type="button"
        ${modalInvoker(UserPasswordLoginLockToggleForm, { instance: user })}
    >
        ${label}
    </button>`;
}
