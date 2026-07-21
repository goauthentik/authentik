import "#admin/users/UserActiveForm";
import "#admin/users/UserForm";
import "#admin/users/UserImpersonateForm";
import "#admin/users/UserPasswordForm";
import "#elements/StatusLabel";

import { userTypeToLabel } from "#common/labels";
import { formatUserDisplayName, startAccountLockdown } from "#common/users";

import { AKElement } from "#elements/Base";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { Timestamp } from "#elements/table/shared";

import { keyValueListStyles, renderKeyValueList } from "#components/KeyValueList";

import { RecoveryButtons } from "#admin/users/recovery";
import { ToggleUserActivationButton } from "#admin/users/UserActiveForm";
import { UserForm } from "#admin/users/UserForm";
import { UserImpersonateForm } from "#admin/users/UserImpersonateForm";
import Styles from "#admin/users/UserInfoCard.css";

import { User, UserTypeEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { CSSResult, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFCard from "@patternfly/patternfly/components/Card/card.css";
import PFContent from "@patternfly/patternfly/components/Content/content.css";

@customElement("ak-user-info-card")
export class UserInfoCard extends AKElement {
    @property({ attribute: false })
    public user?: User;

    @property({ type: Number })
    public currentUserPk?: number;

    @property({ type: Boolean })
    public canImpersonate = false;

    @property({ type: Boolean })
    public hasEnterpriseLicense = false;

    @property({ type: Boolean })
    public brandHasRecoveryFlow = false;

    static styles: CSSResult[] = [PFButton, PFCard, PFContent, keyValueListStyles, Styles];

    protected lockdownUser = async () => {
        if (!this.user) {
            return;
        }

        return startAccountLockdown(this.user.pk).catch(showAPIErrorMessage);
    };

    protected renderActionButtons(user: User) {
        const showImpersonate = this.canImpersonate && user.pk !== this.currentUserPk;
        const showLockdown =
            this.hasEnterpriseLicense &&
            user.pk !== this.currentUserPk &&
            user.type !== UserTypeEnum.InternalServiceAccount;

        const displayName = formatUserDisplayName(user);

        return html`<div class="ak-user-button-collection">
            <button
                class="pf-m-primary pf-c-button pf-m-block"
                ${UserForm.asInstanceInvoker(user.pk)}
            >
                ${msg("Edit User")}
            </button>

            ${ToggleUserActivationButton(user, { className: "pf-m-block" })}
            ${showLockdown
                ? html`<button
                      class="pf-c-button pf-m-danger pf-m-block"
                      @click=${this.lockdownUser}
                      type="button"
                  >
                      ${msg("Account Lockdown")}
                  </button>`
                : nothing}
            ${showImpersonate
                ? html`<button
                      class="pf-c-button pf-m-tertiary pf-m-block"
                      ${UserImpersonateForm.asInstanceInvoker(user.pk)}
                      aria-label=${msg(str`Impersonate ${displayName}`)}
                  >
                      <pf-tooltip
                          position="top"
                          content=${msg("Temporarily assume the identity of this user")}
                      >
                          <span>${msg("Impersonate")}</span>
                      </pf-tooltip>
                  </button>`
                : nothing}
        </div> `;
    }

    protected renderRecoveryButtons(user: User) {
        return html`<div class="ak-user-button-collection">
            ${RecoveryButtons({
                user,
                brandHasRecoveryFlow: this.brandHasRecoveryFlow,
                buttonClasses: "pf-m-block",
                emptyClasses: "ak-user-recovery-empty",
            })}
        </div>`;
    }

    protected renderEmpty() {
        return html`<span class="ak-user-info-empty">-</span>`;
    }

    protected renderDate(value?: Date | null) {
        return value ? Timestamp(value) : this.renderEmpty();
    }

    protected override render() {
        if (!this.user) {
            return nothing;
        }

        const user = this.user;

        return html`
            <div class="pf-c-card__title">${msg("User Info")}</div>
            <div class="pf-c-card__body ak-user-info-body">
                ${renderKeyValueList([
                    [msg("Username"), user.username],
                    [msg("Name"), user.name || this.renderEmpty()],
                    [msg("Email"), user.email || this.renderEmpty()],
                    [msg("Last login"), this.renderDate(user.lastLogin)],
                    [msg("Last password change"), this.renderDate(user.passwordChangeDate)],
                    [
                        msg("Active"),
                        html`<ak-status-label .good=${user.isActive}></ak-status-label>`,
                    ],
                    [msg("Type"), userTypeToLabel(user.type)],
                    [
                        msg("Superuser"),
                        html`<ak-status-label
                            type="neutral"
                            .good=${user.isSuperuser}
                        ></ak-status-label>`,
                    ],
                ])}
                <div class="ak-user-management ak-user-management-divider">
                    <section class="ak-user-management-section">
                        <h3 class="ak-user-management-heading">${msg("Actions")}</h3>
                        ${this.renderActionButtons(user)}
                    </section>
                    <section class="ak-user-management-section">
                        <h3 class="ak-user-management-heading">${msg("Recovery")}</h3>
                        ${this.renderRecoveryButtons(user)}
                    </section>
                </div>
            </div>
        `;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-info-card": UserInfoCard;
    }
}
