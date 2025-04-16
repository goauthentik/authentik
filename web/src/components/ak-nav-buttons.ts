import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
} from "@goauthentik/common/constants";
import { globalAK } from "@goauthentik/common/global";
import { UIConfig, UserDisplay, uiConfig } from "@goauthentik/common/ui/config";
import { me } from "@goauthentik/common/users";
import { AKElement } from "@goauthentik/elements/Base";
import "@goauthentik/elements/buttons/ActionButton/ak-action-button";
import { match } from "ts-pattern";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFBrand from "@patternfly/patternfly/components/Brand/brand.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationBadge from "@patternfly/patternfly/components/NotificationBadge/notification-badge.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

import { CoreApi, EventsApi, SessionUser } from "@goauthentik/api";

@customElement("ak-nav-buttons")
export class NavigationButtons extends AKElement {
    @property({ type: Object })
    uiConfig?: UIConfig;

    @property({ type: Object })
    me?: SessionUser;

    @property({ type: Boolean, reflect: true })
    notificationDrawerOpen = false;

    @property({ type: Boolean, reflect: true })
    apiDrawerOpen = false;

    @property({ type: Number })
    notificationsCount = 0;

    static get styles() {
        return [
            PFBase,
            PFDisplay,
            PFBrand,
            PFPage,
            PFAvatar,
            PFButton,
            PFDrawer,
            PFDropdown,
            PFNotificationBadge,
            css`
                .pf-c-page__header-tools {
                    display: flex;
                }
                :host([theme="dark"]) .pf-c-page__header-tools {
                    color: var(--ak-dark-foreground) !important;
                }
                :host([theme="light"]) .pf-c-page__header-tools-item .fas,
                :host([theme="light"]) .pf-c-notification-badge__count,
                :host([theme="light"]) .pf-c-page__header-tools-group .pf-c-button {
                    color: var(--ak-global--Color--100) !important;
                }

                @media (max-width: 768px) {
                    .pf-c-avatar {
                        display: none;
                    }
                }
            `,
        ];
    }

    async firstUpdated() {
        this.me = await me();
        const notifications = await new EventsApi(DEFAULT_CONFIG).eventsNotificationsList({
            seen: false,
            ordering: "-created",
            pageSize: 1,
            user: this.me.user.pk,
        });
        this.notificationsCount = notifications.pagination.count;
        this.uiConfig = await uiConfig();
    }

    renderApiDrawerTrigger() {
        if (!this.uiConfig?.enabledFeatures.apiDrawer) {
            return nothing;
        }

        const onClick = (ev: Event) => {
            ev.stopPropagation();
            this.dispatchEvent(
                new Event(EVENT_API_DRAWER_TOGGLE, { bubbles: true, composed: true }),
            );
        };

        return html`<div class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-lg">
            <button class="pf-c-button pf-m-plain" type="button" @click=${onClick}>
                <pf-tooltip position="top" content=${msg("Open API drawer")}>
                    <i class="fas fa-code" aria-hidden="true"></i>
                </pf-tooltip>
            </button>
        </div>`;
    }

    renderNotificationDrawerTrigger() {
        if (!this.uiConfig?.enabledFeatures.notificationDrawer) {
            return nothing;
        }

        const onClick = (ev: Event) => {
            ev.stopPropagation();
            this.dispatchEvent(
                new Event(EVENT_NOTIFICATION_DRAWER_TOGGLE, { bubbles: true, composed: true }),
            );
        };

        return html`<div class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-lg">
            <button
                class="pf-c-button pf-m-plain"
                type="button"
                aria-label="${msg("Unread notifications")}"
                @click=${onClick}
            >
                <span
                    class="pf-c-notification-badge ${this.notificationsCount > 0
                        ? "pf-m-unread"
                        : ""}"
                >
                    <pf-tooltip position="top" content=${msg("Open Notification drawer")}>
                        <i class="fas fa-bell" aria-hidden="true"></i>
                    </pf-tooltip>
                    <span class="pf-c-notification-badge__count">${this.notificationsCount}</span>
                </span>
            </button>
        </div> `;
    }

    renderSettings() {
        if (!this.uiConfig?.enabledFeatures.settings) {
            return nothing;
        }

        return html`<div class="pf-c-page__header-tools-item">
            <a
                class="pf-c-button pf-m-plain"
                type="button"
                href="${globalAK().api.base}if/user/#/settings"
            >
                <pf-tooltip position="top" content=${msg("Settings")}>
                    <i class="fas fa-cog" aria-hidden="true"></i>
                </pf-tooltip>
            </a>
        </div>`;
    }

    renderImpersonation() {
        if (!this.me?.original) return nothing;

        const onClick = async () => {
            await new CoreApi(DEFAULT_CONFIG).coreUsersImpersonateEndRetrieve();
            window.location.reload();
        };

        return html`&nbsp;
            <div class="pf-c-page__header-tools">
                <div class="pf-c-page__header-tools-group">
                    <ak-action-button class="pf-m-warning pf-m-small" .apiRequest=${onClick}>
                        ${msg("Stop impersonation")}
                    </ak-action-button>
                </div>
            </div>`;
    }

    renderAvatar() {
        return html`<img
            class="pf-c-avatar"
            src=${ifDefined(this.me?.user.avatar)}
            alt="${msg("Avatar image")}"
        />`;
    }

    get userDisplayName() {
        return match<UserDisplay | undefined, string | undefined>(this.uiConfig?.navbar.userDisplay)
            .with(UserDisplay.username, () => this.me?.user.username)
            .with(UserDisplay.name, () => this.me?.user.name)
            .with(UserDisplay.email, () => this.me?.user.email || "")
            .with(UserDisplay.none, () => "")
            .otherwise(() => this.me?.user.username);
    }

    render() {
        return html`<div class="pf-c-page__header-tools">
            <div class="pf-c-page__header-tools-group">
                ${this.renderApiDrawerTrigger()}
                <!-- -->
                ${this.renderNotificationDrawerTrigger()}
                <!-- -->
                ${this.renderSettings()}
                <div class="pf-c-page__header-tools-item">
                    <a
                        href="${globalAK().api.base}flows/-/default/invalidation/"
                        class="pf-c-button pf-m-plain"
                    >
                        <pf-tooltip position="top" content=${msg("Sign out")}>
                            <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
                        </pf-tooltip>
                    </a>
                </div>
                <slot name="extra"></slot>
            </div>
            ${this.renderImpersonation()}
            ${this.userDisplayName != ""
                ? html`<div class="pf-c-page__header-tools-group">
                      <div class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-md">
                          ${this.userDisplayName}
                      </div>
                  </div>`
                : nothing}
            ${this.renderAvatar()}
        </div>`;
    }
}
