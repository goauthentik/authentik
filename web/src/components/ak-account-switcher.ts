import "#elements/buttons/Dropdown";

import { isAPIResultReady } from "#common/api/responses";
import { globalAK } from "#common/global";
import { formatUserDisplayName } from "#common/users";

import { AKElement } from "#elements/Base";
import { WithSession } from "#elements/mixins/session";
import type { SlottedTemplateResult } from "#elements/types";
import { isDefaultAvatar } from "#elements/utils/images";

import { buildAuthenticationFlowURL } from "#components/ak-account-switcher-url";
import Styles from "#components/ak-account-switcher.css";

import type { AccountSelectionUser } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
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
        return buildAuthenticationFlowURL({
            account,
            accountSelectionFlow: globalAK().brand.flowAccountSelection,
            apiBase: globalAK().api.base,
            next: `${window.location.pathname}${window.location.search}${window.location.hash}`,
        });
    }

    protected renderAvatar(account?: Pick<AccountSelectionUser, "avatar">): SlottedTemplateResult {
        if (account?.avatar && !isDefaultAvatar(account.avatar)) {
            return html`<span part="avatar">
                <img part="avatar-image" src=${account.avatar} alt="" />
            </span>`;
        }
        return html`<span part="avatar">
            <i class="fas fa-user" aria-hidden="true"></i>
        </span>`;
    }

    protected renderAccount(account: AccountSelectionUser): SlottedTemplateResult {
        const label = account.name || account.username;
        const description = account.email || account.username;
        const content = html`
            <span class="pf-c-dropdown__menu-item-main" part="item">
                ${this.renderAvatar(account)}
                <span part="labels">
                    <span part="name">${label}</span>
                    <span part="description">${description}</span>
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
                href=${this.authenticationFlowURL(account)}
            >
                ${content}
            </a>
        </li>`;
    }

    render(): SlottedTemplateResult {
        const currentUser = this.currentUser;
        if (!currentUser) {
            return null;
        }
        const displayName =
            formatUserDisplayName(currentUser, this.uiConfig) || currentUser.username;
        const currentAccount = this.accounts.find((account) => account.isCurrent);

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
                    ${this.accounts.map((account) => this.renderAccount(account))}
                    ${this.accounts.length
                        ? html`<li class="pf-c-dropdown__separator" role="separator"></li>`
                        : null}
                    <li role="presentation">
                        <a
                            class="pf-c-dropdown__menu-item"
                            part="menu-item"
                            role="menuitem"
                            href=${this.authenticationFlowURL()}
                        >
                            <i class="fas fa-plus" aria-hidden="true"></i>
                            ${msg("Add another account", {
                                id: "account-switcher.actions.add-account.label",
                            })}
                        </a>
                    </li>
                    <li role="presentation">
                        <a
                            class="pf-c-dropdown__menu-item"
                            part="menu-item"
                            role="menuitem"
                            href="${globalAK().api.base}flows/-/default/invalidation/"
                        >
                            <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
                            ${msg("Sign out current account", {
                                id: "account-switcher.actions.sign-out-current.label",
                            })}
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
