import "#elements/forms/HorizontalFormElement";
import "#components/ak-switch-input";
import "#elements/buttons/ActionButton/ak-action-button";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { globalAK } from "#common/global";
import { formatUserDisplayName } from "#common/users";

import { AKElement } from "#elements/Base";
import { WithNotifications } from "#elements/mixins/notifications";
import { WithSession } from "#elements/mixins/session";
import { AKDrawerChangeEvent } from "#elements/notifications/events";
import { isDefaultAvatar } from "#elements/utils/images";

import Styles from "#components/ak-nav-button.css";

import { CoreApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFBrand from "@patternfly/patternfly/components/Brand/brand.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationBadge from "@patternfly/patternfly/components/NotificationBadge/notification-badge.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

@customElement("ak-nav-buttons")
export class NavigationButtons extends WithNotifications(WithSession(AKElement)) {
    @property({ type: Boolean, reflect: true })
    notificationDrawerOpen = false;

    @property({ type: Boolean, reflect: true })
    apiDrawerOpen = false;

    static styles = [
        PFBase,
        PFDisplay,
        PFBrand,
        PFPage,
        PFAvatar,
        PFButton,
        PFDrawer,
        PFDropdown,
        PFNotificationBadge,
        Styles,
    ];

    protected renderAPIDrawerTrigger() {
        const { apiDrawer } = this.uiConfig.enabledFeatures;

        return guard([apiDrawer], () => {
            if (!apiDrawer) {
                return nothing;
            }

            return html`<div class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-xl">
                <button
                    id="api-drawer-toggle-button"
                    class="pf-c-button pf-m-plain"
                    type="button"
                    aria-label=${msg("Toggle API requests drawer", {
                        id: "drawer-toggle-button-api-requests",
                    })}
                    @click=${AKDrawerChangeEvent.dispatchAPIToggle}
                >
                    <pf-tooltip
                        position="top"
                        content=${msg("API Drawer")}
                        trigger="api-drawer-toggle-button"
                    >
                        <i class="fas fa-code" aria-hidden="true"></i>
                    </pf-tooltip>
                </button>
            </div>`;
        });
    }

    protected renderNotificationDrawerTrigger() {
        const { notificationDrawer } = this.uiConfig.enabledFeatures;
        const notificationCount = this.notificationCount;

        return guard([notificationDrawer, notificationCount], () => {
            if (!notificationDrawer) {
                return nothing;
            }

            return html`<div class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-xl">
                <button
                    id="notification-drawer-toggle-button"
                    class="pf-c-button pf-m-plain"
                    type="button"
                    aria-label=${msg("Toggle notifications drawer", {
                        id: "drawer-toggle-button-notifications",
                    })}
                    aria-describedby="notification-count"
                    @click=${AKDrawerChangeEvent.dispatchNotificationsToggle}
                >
                    <span class="pf-c-notification-badge ${notificationCount ? "pf-m-unread" : ""}">
                        <pf-tooltip
                            position="top"
                            content=${msg("Notification Drawer", {
                                id: "drawer-invoker-tooltip-notifications",
                            })}
                            trigger="notification-drawer-toggle-button"
                        >
                            <i class="fas fa-bell" aria-hidden="true"></i>
                        </pf-tooltip>
                        <span
                            id="notification-count"
                            class="pf-c-notification-badge__count"
                            aria-live="polite"
                        >
                            ${notificationCount}
                            <span class="sr-only">unread</span>
                        </span>
                    </span>
                </button>
            </div>`;
        });
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
                aria-label=${msg("Settings")}
            >
                <pf-tooltip position="top" content=${msg("Settings")}>
                    <i class="fas fa-cog" aria-hidden="true"></i>
                </pf-tooltip>
            </a>
        </div>`;
    }

    renderImpersonation() {
        if (!this.impersonating) return nothing;

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
        const { currentUser } = this;

        if (!currentUser) {
            return nothing;
        }

        const { avatar } = currentUser;

        if (!avatar || isDefaultAvatar(avatar)) {
            return nothing;
        }

        return html`<div
            class="pf-c-page__header-tools-item pf-c-avatar pf-m-hidden pf-m-visible-on-xl"
            aria-hidden="true"
        >
            <img src=${avatar} alt=${msg("Avatar image")} />
        </div>`;
    }

    render() {
        const displayName = formatUserDisplayName(this.currentUser, this.uiConfig);

        return html`<div role="presentation" class="pf-c-page__header-tools">
            <div class="pf-c-page__header-tools-group">
                ${this.renderAPIDrawerTrigger()}
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
            ${displayName
                ? html`<div class="pf-c-page__header-tools-group pf-m-hidden">
                      <div class="pf-c-page__header-tools-item pf-m-visible-on-2xl">
                          ${displayName}
                      </div>
                  </div>`
                : nothing}
            ${this.renderAvatar()}
        </div>`;
    }
}
