import "#elements/buttons/Dropdown";

import { globalAK } from "#common/global";
import { formatUserDisplayName, formatUserSecondaryIdentifier } from "#common/users";

import { AKElement } from "#elements/Base";
import { WithSession } from "#elements/mixins/session";
import type { SlottedTemplateResult } from "#elements/types";
import { isDefaultAvatar } from "#elements/utils/images";

import { type BrowserLocalUser, syncStoredUsers } from "#components/ak-user-switcher-storage";
import Styles from "#components/ak-user-switcher.css";

import { msg } from "@lit/localize";
import { html, type PropertyValues } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";

@customElement("ak-user-switcher")
export class UserSwitcher extends WithSession(AKElement) {
    static styles = [PFButton, PFDropdown, Styles];

    protected users: BrowserLocalUser[] = [];

    protected override willUpdate(changed: PropertyValues<this>): void {
        super.willUpdate(changed);
        if (changed.has("session")) {
            this.users = syncStoredUsers(this.currentUser);
        }
    }

    protected get nextQuery(): string {
        const next = `${window.location.pathname}${window.location.search}${window.location.hash}`;
        return new URLSearchParams({ next }).toString();
    }

    protected rootURL(path: string, query?: string): string {
        const base = new URL(globalAK().api.base, window.location.origin);
        if (!base.pathname.endsWith("/")) {
            base.pathname = `${base.pathname}/`;
        }
        const url = new URL(path, base);
        if (query) {
            url.search = query;
        }
        return `${url.pathname}${url.search}${url.hash}`;
    }

    protected userSwitchURL(user: BrowserLocalUser): string {
        return this.rootURL(`user/switch/${user.pk}/`, this.nextQuery);
    }

    protected addUserURL(): string {
        return this.rootURL("flows/-/default/authentication/", this.nextQuery);
    }

    protected get currentLocalUser(): BrowserLocalUser | undefined {
        return this.users.find((user) => user.isCurrent);
    }

    protected get userSwitchingEnabled(): boolean {
        return Boolean(globalAK().brand.flowUserSwitch);
    }

    protected userLabel(user: BrowserLocalUser): string {
        return formatUserDisplayName(user, this.uiConfig) || user.username;
    }

    protected renderAvatar(user?: { avatar?: string }): SlottedTemplateResult {
        if (user?.avatar && !isDefaultAvatar(user.avatar)) {
            return html`<span part="avatar">
                <img part="avatar-image" src=${user.avatar} alt="" />
            </span>`;
        }
        return html`<span part="avatar">
            <i class="fas fa-user" aria-hidden="true"></i>
        </span>`;
    }

    protected renderUser(user: BrowserLocalUser): SlottedTemplateResult {
        const label = this.userLabel(user);
        const description = formatUserSecondaryIdentifier(user, label);

        const content = html`<span class="pf-c-dropdown__menu-item-main" part="item">
            ${this.renderAvatar(user)}
            <span part="labels">
                <span part="name">${label}</span>
                ${description ? html`<span part="description">${description}</span>` : null}
            </span>
            ${user.isCurrent
                ? html`<i class="fas fa-check" part="current-indicator" aria-hidden="true"></i>`
                : null}
        </span>`;

        if (user.isCurrent) {
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
                href=${this.userSwitchURL(user)}
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
            href=${this.rootURL("flows/-/default/invalidation/")}
        >
            <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
            ${msg("Sign out current user", {
                id: "user-switcher.actions.sign-out-current.label",
            })}
        </a>`;
    }

    render(): SlottedTemplateResult {
        if (!this.currentUser) {
            return null;
        }

        // When the brand has no user-switch flow configured, switching is disabled and
        // the backend rejects it, so only surface the current user and hide the switch
        // targets and the add-user action.
        const users = this.userSwitchingEnabled
            ? this.users
            : this.users.filter((user) => user.isCurrent);

        return html`<div part="container">
            <ak-dropdown class="pf-c-dropdown" part="switcher">
                <button
                    class="pf-c-dropdown__toggle pf-m-plain"
                    part="toggle"
                    type="button"
                    id="user-switcher-toggle"
                    aria-haspopup="menu"
                    aria-controls="user-switcher-menu"
                    aria-label=${msg("Switch user", {
                        id: "user-switcher.toggle.label",
                    })}
                >
                    ${this.renderAvatar(this.currentLocalUser)}
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
                    id="user-switcher-menu"
                    aria-labelledby="user-switcher-toggle"
                    tabindex="-1"
                >
                    ${users.map((user) => this.renderUser(user))}
                    ${users.length
                        ? html`<li class="pf-c-dropdown__separator" role="separator"></li>`
                        : null}
                    ${this.userSwitchingEnabled
                        ? html`<li role="presentation">
                              <a
                                  class="pf-c-dropdown__menu-item"
                                  part="menu-item"
                                  role="menuitem"
                                  href=${this.addUserURL()}
                              >
                                  <i class="fas fa-plus" aria-hidden="true"></i>
                                  ${msg("Add another user", {
                                      id: "user-switcher.actions.add-user.label",
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
        "ak-user-switcher": UserSwitcher;
    }
}
