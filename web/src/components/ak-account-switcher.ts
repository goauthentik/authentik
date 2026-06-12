import "#elements/buttons/Dropdown";

import { globalAK } from "#common/global";
import { formatUserDisplayName, formatUserSecondaryIdentifier } from "#common/users";

import { AKElement } from "#elements/Base";
import { WithSession } from "#elements/mixins/session";
import type { SlottedTemplateResult } from "#elements/types";
import { isDefaultAvatar } from "#elements/utils/images";

import {
    accountFromUser,
    type BrowserLocalAccount,
    readStoredAccounts,
    writeStoredAccounts,
} from "#components/ak-account-switcher-storage";
import Styles from "#components/ak-account-switcher.css";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";

@customElement("ak-account-switcher")
export class AccountSwitcher extends WithSession(AKElement) {
    static styles = [PFButton, PFDropdown, Styles];

    protected get accounts(): BrowserLocalAccount[] {
        const currentUser = this.currentUser;
        if (!currentUser) {
            return readStoredAccounts();
        }
        const currentAccount = accountFromUser(currentUser);
        const accounts = [
            currentAccount,
            ...readStoredAccounts()
                .filter((account) => account.uid !== currentAccount.uid)
                .map((account) => ({ ...account, isCurrent: false })),
        ];
        writeStoredAccounts(accounts);
        return accounts;
    }

    protected nextQuery(): string {
        const next = `${window.location.pathname}${window.location.search}${window.location.hash}`;
        return new URLSearchParams({ next }).toString();
    }

    protected accountSwitchURL(account: BrowserLocalAccount): string {
        return `${globalAK().api.base}account/switch/${account.uid}/?${this.nextQuery()}`;
    }

    protected addAccountURL(): string {
        return `${globalAK().api.base}flows/-/default/authentication/?${this.nextQuery()}`;
    }

    protected renderAvatar(account?: Pick<BrowserLocalAccount, "avatar">): SlottedTemplateResult {
        if (account?.avatar && !isDefaultAvatar(account.avatar)) {
            return html`<span part="avatar">
                <img part="avatar-image" src=${account.avatar} alt="" />
            </span>`;
        }
        return html`<span part="avatar">
            <i class="fas fa-user" aria-hidden="true"></i>
        </span>`;
    }

    protected renderAccount(account: BrowserLocalAccount): SlottedTemplateResult {
        const label = account.name || account.username;
        const description = formatUserSecondaryIdentifier(account, label);
        const content = html`
            <span class="pf-c-dropdown__menu-item-main" part="item">
                ${this.renderAvatar(account)}
                <span part="labels">
                    <span part="name">${label}</span>
                    ${description ? html`<span part="description">${description}</span>` : null}
                </span>
                ${account.isCurrent
                    ? html`<i class="fas fa-check" part="current-indicator" aria-hidden="true"></i>`
                    : null}
            </span>
        `;

        if (account.isCurrent) {
            return html`<li role="presentation">
                <button class="pf-c-dropdown__menu-item" part="menu-item" role="menuitem" disabled>
                    ${content}
                </button>
            </li>`;
        }

        return html`<li role="presentation">
            <a
                class="pf-c-dropdown__menu-item"
                part="menu-item"
                role="menuitem"
                href=${this.accountSwitchURL(account)}
            >
                ${content}
            </a>
        </li>`;
    }

    protected renderSignOut(): SlottedTemplateResult {
        return html`<a
            class="pf-c-dropdown__menu-item"
            part="menu-item"
            role="menuitem"
            href="${globalAK().api.base}flows/-/default/invalidation/"
        >
            <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
            ${msg("Sign out current account", {
                id: "account-switcher.actions.sign-out-current.label",
            })}
        </a>`;
    }

    render(): SlottedTemplateResult {
        const currentUser = this.currentUser;
        if (!currentUser) {
            return null;
        }
        // Switching only works through the brand's account switch flow; without
        // one, offer plain sign out instead of a list that leads nowhere.
        const switchingAvailable = Boolean(globalAK().brand.flowAccountSwitch);
        const accounts = switchingAvailable ? this.accounts : [];
        const displayName =
            formatUserDisplayName(currentUser, this.uiConfig) || currentUser.username;
        const currentAccount = accounts.find((account) => account.isCurrent);

        return html`<div part="container">
            <ak-dropdown class="pf-c-dropdown" part="switcher">
                <button
                    class="pf-c-dropdown__toggle pf-m-plain"
                    part="toggle"
                    type="button"
                    id="account-switcher-toggle"
                    aria-haspopup="menu"
                    aria-controls="account-switcher-menu"
                >
                    ${this.renderAvatar(currentAccount)}
                    <span part="toggle-label">${displayName}</span>
                    <i
                        class="fas fa-caret-down pf-c-dropdown__toggle-icon"
                        part="toggle-icon"
                        aria-hidden="true"
                    ></i>
                </button>
                <menu
                    class="pf-c-dropdown__menu pf-m-align-right"
                    part="menu"
                    hidden
                    id="account-switcher-menu"
                    aria-labelledby="account-switcher-toggle"
                    tabindex="-1"
                >
                    ${accounts.map((account) => this.renderAccount(account))}
                    ${accounts.length
                        ? html`<li class="pf-c-dropdown__separator" role="separator"></li>`
                        : null}
                    ${switchingAvailable
                        ? html`<li role="presentation">
                              <a
                                  class="pf-c-dropdown__menu-item"
                                  part="menu-item"
                                  role="menuitem"
                                  href=${this.addAccountURL()}
                              >
                                  <i class="fas fa-plus" aria-hidden="true"></i>
                                  ${msg("Add another account", {
                                      id: "account-switcher.actions.add-account.label",
                                  })}
                              </a>
                          </li>`
                        : null}
                    <li role="presentation">${this.renderSignOut()}</li>
                </menu>
            </ak-dropdown>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-account-switcher": AccountSwitcher;
    }
}
