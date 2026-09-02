import "#elements/buttons/Dropdown";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

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

import { msg, str } from "@lit/localize";
import { html, PropertyValues } from "lit";
import { customElement, state } from "lit/decorators.js";
import { repeat } from "lit/directives/repeat.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDivider from "@patternfly/patternfly/components/Divider/divider.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

@customElement("ak-user-switcher")
export class UserSwitcher extends WithSession(AKElement) {
    public static styles = [
        // ---
        PFButton,
        PFDropdown,
        PFDivider,
        PFDisplay,
        Styles,
    ];

    @state()
    protected userSwitcherVisible: boolean = false;

    @state()
    protected users: readonly UserSelf[] = [];

    protected override updated(changed: PropertyValues<this>): void {
        super.updated(changed);

        if (changed.has("session")) {
            this.synchronizeUserSwitcherVisibility();
        }
    }

    protected synchronizeUserSwitcherVisibility(): void {
        const allUsers: readonly UserSelf[] = isAPIResultReady(this.session)
            ? [this.session.user, ...(this.session.users ?? [])]
            : [];

        this.userSwitcherVisible = !!globalAK().brand.flowUserSwitch;

        this.users = this.userSwitcherVisible
            ? allUsers
            : allUsers.filter((user) => user.isCurrent);
    }

    protected startSwitch = async (userPk?: number): Promise<void> => {
        const { pathname, search, hash } = window.location;
        const next = `${pathname}${search}${hash}`;

        const { redirect } = await aki(CoreApi).coreUsersSwitchCreate({
            next,
            userSwitchRequest: {
                action:
                    userPk === undefined ? UserSwitchActionEnum.Add : UserSwitchActionEnum.Switch,
                userPk,
            },
        });

        window.location.assign(redirect);
    };

    protected renderAvatar(user?: { avatar?: string }): SlottedTemplateResult {
        if (user?.avatar && !isDefaultAvatar(user.avatar)) {
            return html`<div part="avatar">
                <img
                    part="avatar-image"
                    src=${user.avatar}
                    alt=${msg("User avatar", { id: "user-switcher.avatar.alt" })}
                />
                <div part="avatar-overlay" data-tooltip-target></div>
            </div>`;
        }
        return html`<div part="avatar">
            <i class="fas fa-user" aria-hidden="true"></i>
        </div>`;
    }

    protected renderUser(user: UserSelf): SlottedTemplateResult {
        const label = formatUserDisplayName(user, this.uiConfig) || user.username;
        const description = [user.email, user.username].find(
            (identifier) => identifier && identifier !== label,
        );

        const current = user.isCurrent;

        return html`<li role="presentation">
            <button
                class="pf-c-dropdown__menu-item"
                part="menu-item user"
                role="menuitem"
                type="button"
                ?disabled=${current}
                @click=${() => this.startSwitch(user.pk)}
                aria-label=${current
                    ? msg(str`Current user "${label}"`, {
                          id: "user-switcher.actions.current-user.label",
                      })
                    : msg(str`Switch to user "${label}"`, {
                          id: "user-switcher.actions.switch-to-user.label",
                      })}
            >
                <div class="pf-c-dropdown__menu-item-main" part="item user">
                    ${this.renderAvatar(user)}
                    <div part="labels">
                        <div part="name">${label}</div>
                        ${description ? html`<div part="description">${description}</div>` : null}
                    </div>
                    ${current
                        ? html`<i
                              class="fas fa-check pf-u-display-none pf-u-display-block-on-sm"
                              part="current-indicator"
                              aria-hidden="true"
                          ></i>`
                        : null}
                </div>
            </button>
        </li>`;
    }

    render(): SlottedTemplateResult {
        if (!this.currentUser) {
            return null;
        }

        return html`<ak-dropdown class="pf-c-dropdown" part="switcher">
            <button
                class="pf-c-dropdown__toggle pf-m-plain"
                part="toggle"
                type="button"
                id="user-switcher-toggle"
                aria-haspopup="menu"
                aria-controls="user-switcher-menu"
                aria-label=${msg("Toggle user navigation menu", {
                    id: "user-switcher.toggle.tooltip",
                })}
            >
                <pf-tooltip
                    part="toggle-tooltip"
                    position="top-end"
                    content=${msg("Open user navigation menu", {
                        id: "user-switcher.open.tooltip",
                    })}
                    aria-hidden="true"
                >
                    ${this.renderAvatar(this.currentUser)}
                </pf-tooltip>
            </button>

            <menu
                class="pf-c-dropdown__menu pf-m-align-right"
                part="menu"
                hidden
                id="user-switcher-menu"
                aria-labelled=${msg("User navigation menu", { id: "user-switcher.menu.label" })}
                tabindex="-1"
            >
                ${repeat(
                    this.users,
                    (user) => user.pk,
                    (user) => this.renderUser(user),
                )}
                ${this.users.length ? html`<li class="pf-c-divider" role="separator"></li>` : null}
                ${this.userSwitcherVisible
                    ? html`<li role="presentation">
                          <button
                              class="pf-c-dropdown__menu-item"
                              part="menu-item"
                              role="menuitem"
                              type="button"
                              @click=${() => this.startSwitch()}
                          >
                              <i class="fas fa-plus" aria-hidden="true"></i>
                              ${msg("Add another user", {
                                  id: "user-switcher.actions.add-user.label",
                              })}
                          </button>
                      </li>`
                    : null}
                <li role="presentation">
                    <a
                        class="pf-c-dropdown__menu-item"
                        part="menu-item"
                        role="menuitem"
                        href=${`${globalAK().api.base}flows/-/default/invalidation/`}
                    >
                        <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
                        ${msg("Sign out current user", {
                            id: "user-switcher.actions.sign-out-current.label",
                        })}
                    </a>
                </li>
            </menu>
        </ak-dropdown>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-user-switcher": UserSwitcher;
    }
}
