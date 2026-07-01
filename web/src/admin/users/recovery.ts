import { formatUserDisplayName } from "#common/users";

import { modalInvoker } from "#elements/dialogs";
import { LitFC } from "#elements/types";

import { UserPasswordForm } from "#admin/users/UserPasswordForm";
import { UserRecoveryLinkForm } from "#admin/users/UserRecoveryLinkForm";
import { UserResetEmailForm } from "#admin/users/UserResetEmailForm";

import { User } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { html } from "lit";

export interface RecoveryButtonsProps {
    user: User;
    brandHasRecoveryFlow: boolean;
    buttonClasses?: string;
    emptyClasses?: string;
}

export const RecoveryButtons: LitFC<RecoveryButtonsProps> = ({
    user,
    brandHasRecoveryFlow,
    buttonClasses,
    emptyClasses,
}: RecoveryButtonsProps) => {
    const recoveryModals = brandHasRecoveryFlow
        ? [
              html`<button
                  class="pf-c-button pf-m-secondary ${buttonClasses || ""}"
                  ${modalInvoker(UserRecoveryLinkForm, { user })}
              >
                  ${msg("Create recovery link")}
              </button>`,

              user.email
                  ? html`<button
                        class="pf-c-button pf-m-secondary ${buttonClasses || ""}"
                        ${modalInvoker(UserResetEmailForm, { user })}
                    >
                        ${msg("Email recovery link")}
                    </button>`
                  : html`<p>
                        <span class=${emptyClasses || ""}>${msg("No email address set.")}</span>
                    </p>`,
          ]
        : [
              html`<p>
                  <span class=${emptyClasses || ""}>
                      ${msg("No recovery flow configured for this brand.")}
                  </span>
              </p>`,
          ];

    return [
        html`<button
            class="pf-c-button pf-m-secondary ${buttonClasses || ""}"
            type="button"
            ${modalInvoker(UserPasswordForm, {
                headline: msg(str`Update ${formatUserDisplayName(user)}'s password`),
                username: user.username,
                email: user.email,
                instancePk: user.pk,
            })}
        >
            ${msg("Set password")}
        </button>`,
        ...recoveryModals,
    ];
};
