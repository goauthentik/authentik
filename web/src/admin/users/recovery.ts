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
}

export const RecoveryButtons: LitFC<RecoveryButtonsProps> = ({
    user,
    brandHasRecoveryFlow,
    buttonClasses,
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
                        ${msg("To email a recovery link, set an email address for this user.")}
                    </p>`,
          ]
        : [
              html`<p>
                  ${msg("To create a recovery link, set a recovery flow for the current brand.")}
              </p>`,
          ];

    return [
        html`<button
            class="pf-c-button pf-m-secondary ${buttonClasses || ""}"
            type="button"
            ${modalInvoker(UserPasswordForm, {
                headline: msg(str`Update ${user.name || user.username}'s password`),
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
