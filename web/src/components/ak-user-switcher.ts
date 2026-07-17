import "#elements/buttons/Dropdown";

import { aki } from "#common/api/client";
import { isAPIResultReady } from "#common/api/responses";
import { globalAK } from "#common/global";
import { formatUserDisplayName } from "#common/users";

import { AKElement } from "#elements/Base";
import { WithSession } from "#elements/mixins/session";
import type { SlottedTemplateResult } from "#elements/types";
import { isDefaultAvatar } from "#elements/utils/images";

import Styles from "#components/ak-user-switcher.css";

import { CoreApi, type UserSelf, UserSwitchActionEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html } from "lit";
import { customElement } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";

@customElement("ak-user-switcher")
export class UserSwitcher extends WithSession(AKElement) {
    static styles = [PFButton, PFDropdown, Styles];

    get #users(): readonly UserSelf[] {
        return isAPIResultReady(this.session)
            ? [this.session.user, ...(this.session.users ?? [])]
            : [];
    }

    async #startSwitch(userPk?: number): Promise<void> {
        const { redirect } = await aki(CoreApi).coreUsersSwitchCreate({
            next: `${window.location.pathname}${window.location.search}${window.location.hash}`,
            userSwitchRequest: {
                action:
                    userPk === undefined ? UserSwitchActionEnum.Add : UserSwitchActionEnum.Switch,
                userPk,
            },
        });
        window.location.assign(redirect);
    }

    #renderAvatar(user?: { avatar?: string }): SlottedTemplateResult {
        if (user?.avatar && !isDefaultAvatar(user.avatar)) {
            return html`<span part="avatar">
                <img part="avatar-image" src=${user.avatar} alt="" />
            </span>`;
        }
        return html`<span part="avatar">
            <i class="fas fa-user" aria-hidden="true"></i>
        </span>`;
    }

    #renderUser(user: UserSelf): SlottedTemplateResult {
        const label = formatUserDisplayName(user, this.uiConfig) || user.username;
        const description =
            [user.email, user.username].find((identifier) => identifier && identifier !== label) ??
            "";

        return html`<li role="presentation">
            <button
                class="pf-c-dropdown__menu-item"
                part="menu-item"
                role="menuitem"
                type="button"
                ?disabled=${user.isCurrent}
                @click=${() => this.#startSwitch(user.pk)}
            >
                <span class="pf-c-dropdown__menu-item-main" part="item">
                    ${this.#renderAvatar(user)}
                    <span part="labels">
                        <span part="name">${label}</span>
                        ${description ? html`<span part="description">${description}</span>` : null}
                    </span>
                    ${user.isCurrent
                        ? html`<i
                              class="fas fa-check"
                              part="current-indicator"
                              aria-hidden="true"
                          ></i>`
                        : null}
                </span>
            </button>
        </li>`;
    }

    #renderSignOut(): SlottedTemplateResult {
        return html`<a
            class="pf-c-dropdown__menu-item"
            part="menu-item"
            role="menuitem"
            href=${`${globalAK().api.base}flows/-/default/invalidation/`}
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

        const enabled = Boolean(globalAK().brand.flowUserSwitch);
        const users = enabled ? this.#users : this.#users.filter((user) => user.isCurrent);

        return html`<ak-dropdown class="pf-c-dropdown" part="switcher">
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
                ${this.#renderAvatar(this.currentUser)}
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
                ${users.map((user) => this.#renderUser(user))}
                ${users.length
                    ? html`<li class="pf-c-dropdown__separator" role="separator"></li>`
                    : null}
                ${enabled
                    ? html`<li role="presentation">
                          <button
                              class="pf-c-dropdown__menu-item"
                              part="menu-item"
                              role="menuitem"
                              type="button"
                              @click=${() => this.#startSwitch()}
                          >
                              <i class="fas fa-plus" aria-hidden="true"></i>
                              ${msg("Add another user", {
                                  id: "user-switcher.actions.add-user.label",
                              })}
                          </button>
                      </li>`
                    : null}
                <li role="presentation">${this.#renderSignOut()}</li>
            </menu>
        </ak-dropdown>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-switcher": UserSwitcher;
    }
}
