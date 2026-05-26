import "#elements/buttons/Dropdown";

import { isAPIResultReady } from "#common/api/responses";
import { globalAK } from "#common/global";
import { formatUserDisplayName } from "#common/users";

import { AKElement } from "#elements/Base";
import { WithSession } from "#elements/mixins/session";
import { isDefaultAvatar } from "#elements/utils/images";

import Styles from "#components/ak-account-switcher.css";

import type { AccountSelectionUser } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";

@customElement("ak-account-switcher")
export class AccountSwitcher extends WithSession(AKElement) {
    static styles = [PFButton, PFDropdown, Styles];

    protected get accounts(): AccountSelectionUser[] {
        if (!isAPIResultReady(this.session)) {
            return [];
        }
        return this.session.accounts ?? [];
    }

    protected authenticationFlowURL(account?: AccountSelectionUser): string {
        const query = new URLSearchParams({
            next: `${window.location.pathname}${window.location.search}${window.location.hash}`,
        });
        const loginHint = account?.email || account?.username;
        const accountSelectionFlow = globalAK().brand.flowAccountSelection;
        if (account?.uid && accountSelectionFlow) {
            query.set("account_uid", account.uid);
            return `${globalAK().api.base}if/flow/${accountSelectionFlow}/?${query.toString()}`;
        }
        if (!account?.uid) {
            query.set("add_account", "true");
        }
        if (loginHint) {
            query.set("login_hint", loginHint);
        }
        return `${globalAK().api.base}flows/-/default/authentication/?${query.toString()}`;
    }

    protected renderAvatar(account?: Pick<AccountSelectionUser, "avatar">) {
        if (account?.avatar && !isDefaultAvatar(account.avatar)) {
            return html`<span class="account-switcher-avatar">
                <img src=${account.avatar} alt="" />
            </span>`;
        }
        return html`<span class="account-switcher-avatar">
            <i class="fas fa-user" aria-hidden="true"></i>
        </span>`;
    }

    protected renderAccount(account: AccountSelectionUser) {
        const label = account.name || account.username;
        const description = account.email || account.username;
        const content = html`
            <span class="pf-c-dropdown__menu-item-main account-switcher-item">
                ${this.renderAvatar(account)}
                <span class="account-switcher-labels">
                    <span class="account-switcher-name">${label}</span>
                    <span class="account-switcher-description">${description}</span>
                </span>
                ${account.isCurrent
                    ? html`<i class="fas fa-check account-switcher-current" aria-hidden="true"></i>`
                    : nothing}
            </span>
        `;

        if (account.isCurrent) {
            return html`<li role="presentation">
                <button class="pf-c-dropdown__menu-item" role="menuitem" disabled>
                    ${content}
                </button>
            </li>`;
        }

        return html`<li role="presentation">
            <a
                class="pf-c-dropdown__menu-item"
                role="menuitem"
                href=${this.authenticationFlowURL(account)}
            >
                ${content}
            </a>
        </li>`;
    }

    render() {
        const currentUser = this.currentUser;
        if (!currentUser) {
            return nothing;
        }
        const displayName = formatUserDisplayName(currentUser, this.uiConfig) || currentUser.username;
        const currentAccount = this.accounts.find((account) => account.isCurrent);

        return html`<div class="account-switcher-container">
            <ak-dropdown class="pf-c-dropdown account-switcher">
                <button
                    class="pf-c-dropdown__toggle pf-m-plain account-switcher-toggle"
                    type="button"
                    id="account-switcher-toggle"
                    aria-haspopup="menu"
                    aria-controls="account-switcher-menu"
                >
                    ${this.renderAvatar(currentAccount)}
                    <span class="account-switcher-toggle-label">${displayName}</span>
                    <i class="fas fa-caret-down pf-c-dropdown__toggle-icon" aria-hidden="true"></i>
                </button>
                <menu
                    class="pf-c-dropdown__menu pf-m-align-right"
                    hidden
                    id="account-switcher-menu"
                    aria-labelledby="account-switcher-toggle"
                    tabindex="-1"
                >
                    ${this.accounts.map((account) => this.renderAccount(account))}
                    ${this.accounts.length
                        ? html`<li class="pf-c-dropdown__separator" role="separator"></li>`
                        : nothing}
                    <li role="presentation">
                        <a
                            class="pf-c-dropdown__menu-item"
                            role="menuitem"
                            href=${this.authenticationFlowURL()}
                        >
                            <i class="fas fa-plus" aria-hidden="true"></i>
                            ${msg("Add another account")}
                        </a>
                    </li>
                    <li role="presentation">
                        <a
                            class="pf-c-dropdown__menu-item"
                            role="menuitem"
                            href="${globalAK().api.base}flows/-/default/invalidation/"
                        >
                            <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
                            ${msg("Sign out current account")}
                        </a>
                    </li>
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
