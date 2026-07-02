import "#admin/users/UserActiveForm";
import "#admin/users/UserForm";
import "#admin/users/UserImpersonateForm";
import "#admin/users/UserPasswordForm";
import "#components/ak-status-label";

import { userTypeToLabel } from "#common/labels";
import { formatUserDisplayName, startAccountLockdown } from "#common/users";

import { AKElement } from "#elements/Base";
import { showAPIErrorMessage } from "#elements/messages/MessageContainer";
import { Timestamp } from "#elements/table/shared";
import type { SlottedTemplateResult } from "#elements/types";

import { RecoveryButtons } from "#admin/users/recovery";
import { ToggleUserActivationButton } from "#admin/users/UserActiveForm";
import { UserForm } from "#admin/users/UserForm";
import { UserImpersonateForm } from "#admin/users/UserImpersonateForm";

import { User, UserTypeEnum } from "@goauthentik/api";

import { msg, str } from "@lit/localize";
import { css, CSSResult, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

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

    @state()
    private narrowLayout = false;

    #resizeObserver?: ResizeObserver;

    static styles: CSSResult[] = [
        PFButton,
        PFCard,
        PFContent,
        css`
            :host {
                display: block;
            }

            .ak-user-info-body {
                display: grid;
                gap: var(--pf-global--spacer--lg);
            }

            .ak-user-info-grid {
                display: grid;
                column-gap: var(--pf-global--spacer--xl);
                grid-template-columns: repeat(2, minmax(0, 1fr));
                row-gap: var(--pf-global--spacer--sm);
            }

            .ak-user-info-grid-one-column {
                grid-template-columns: minmax(0, 1fr);
            }

            .ak-user-info-row {
                align-items: center;
                column-gap: var(--pf-global--spacer--md);
                display: grid;
                grid-template-columns: minmax(6.5rem, 40%) minmax(0, 1fr);
                min-height: 2rem;
            }

            .ak-user-info-label {
                align-items: center;
                color: var(--pf-global--Color--200);
                display: flex;
                font-size: var(--pf-global--FontSize--sm);
                font-weight: var(--pf-global--FontWeight--bold);
                line-height: 1.3;
            }

            .ak-user-info-value {
                align-items: center;
                display: flex;
                min-width: 0;
                overflow-wrap: anywhere;
            }

            .ak-user-info-empty {
                color: var(--pf-global--Color--200);
            }

            .ak-user-recovery-empty {
                color: var(--pf-global--Color--200);
                font-size: var(--pf-global--FontSize--sm);
            }

            .ak-user-management {
                display: grid;
                gap: var(--pf-global--spacer--md);
                grid-template-columns: repeat(auto-fit, minmax(13rem, 1fr));
            }

            .ak-user-management-section {
                min-width: 0;
            }

            .ak-user-management-heading {
                color: var(--pf-global--Color--200);
                font-size: var(--pf-global--FontSize--sm);
                font-weight: var(--pf-global--FontWeight--bold);
                margin: 0 0 var(--pf-global--spacer--sm);
            }

            .ak-user-management-divider {
                border-top: 1px solid var(--pf-global--BorderColor--100);
                padding-top: var(--pf-global--spacer--lg);
            }

            .ak-user-button-collection {
                display: flex;
                flex-direction: column;
                gap: 0.375rem;
            }

            .ak-user-button-collection > * {
                flex: 1 0 100%;
            }

            @media (max-width: 768px) {
                .ak-user-info-grid {
                    grid-template-columns: minmax(0, 1fr);
                }
            }
        `,
    ];

    public override connectedCallback() {
        super.connectedCallback();

        this.#resizeObserver = new ResizeObserver(([entry]) => {
            this.narrowLayout = entry.contentRect.width < 512;
        });
        this.#resizeObserver.observe(this);
    }

    public override disconnectedCallback() {
        this.#resizeObserver?.disconnect();
        super.disconnectedCallback();
    }

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

    protected renderInfoItem(label: string, value: SlottedTemplateResult) {
        return html`<div class="ak-user-info-row">
            <div class="ak-user-info-label">${label}</div>
            <div class="ak-user-info-value">${value}</div>
        </div>`;
    }

    protected override render() {
        if (!this.user) {
            return nothing;
        }

        const user = this.user;

        return html`
            <div class="pf-c-card__title">${msg("User Info")}</div>
            <div class="pf-c-card__body ak-user-info-body">
                <div
                    class="ak-user-info-grid ${this.narrowLayout
                        ? "ak-user-info-grid-one-column"
                        : ""}"
                >
                    ${this.renderInfoItem(msg("Username"), user.username)}
                    ${this.renderInfoItem(msg("Name"), user.name || this.renderEmpty())}
                    ${this.renderInfoItem(msg("Email"), user.email || this.renderEmpty())}
                    ${this.renderInfoItem(msg("Last login"), this.renderDate(user.lastLogin))}
                    ${this.renderInfoItem(
                        msg("Last password change"),
                        this.renderDate(user.passwordChangeDate),
                    )}
                    ${this.renderInfoItem(
                        msg("Active"),
                        html`<ak-status-label .good=${user.isActive}></ak-status-label>`,
                    )}
                    ${this.renderInfoItem(msg("Type"), userTypeToLabel(user.type))}
                    ${this.renderInfoItem(
                        msg("Superuser"),
                        html`<ak-status-label
                            type="neutral"
                            .good=${user.isSuperuser}
                        ></ak-status-label>`,
                    )}
                </div>
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
