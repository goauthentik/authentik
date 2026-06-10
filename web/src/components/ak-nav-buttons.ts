import "#components/ak-account-switcher";
import "#elements/forms/HorizontalFormElement";
import "#components/ak-switch-input";
import "#elements/buttons/ActionButton/ak-action-button";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { aki } from "#common/api/client";
import { globalAK } from "#common/global";

import { AKElement } from "#elements/Base";
import { WithNotifications } from "#elements/mixins/notifications";
import { WithSession } from "#elements/mixins/session";

import Styles from "#components/ak-nav-button.css";
import { AKDrawerChangeEvent } from "#components/notifications/events";

import { CoreApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";
import { guard } from "lit/directives/guard.js";

import PFBrand from "@patternfly/patternfly/components/Brand/brand.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFNotificationBadge from "@patternfly/patternfly/components/NotificationBadge/notification-badge.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

@customElement("ak-nav-buttons")
export class NavigationButtons extends WithNotifications(WithSession(AKElement)) {
    @property({ type: Boolean, reflect: true })
    notificationDrawerOpen = false;

    @property({ type: Boolean, reflect: true })
    apiDrawerOpen = false;

    static styles = [PFDisplay, PFBrand, PFPage, PFButton, PFDrawer, PFNotificationBadge, Styles];

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
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            class="ak-c-vector-icon"
                            fill="currentColor"
                            aria-hidden="true"
                            viewBox="0 0 32 32"
                        >
                            <path
                                d="M8 9H4a2 2 0 0 0-2 2v12h2v-5h4v5h2V11a2 2 0 0 0-2-2m-4 7v-5h4v5ZM22 11h3v10h-3v2h8v-2h-3V11h3V9h-8zM14 23h-2V9h6a2 2 0 0 1 2 2v5a2 2 0 0 1-2 2h-4Zm0-7h4v-5h-4Z"
                            />
                        </svg>
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
            await aki(CoreApi).coreUsersImpersonateEndRetrieve();
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

    render() {
        return html`<div role="presentation" class="pf-c-page__header-tools">
            <div class="pf-c-page__header-tools-group">
                ${this.renderAPIDrawerTrigger()}
                <!-- -->
                ${this.renderNotificationDrawerTrigger()}
                <!-- -->
                ${this.renderSettings()}
                <ak-account-switcher></ak-account-switcher>
                <slot name="extra"></slot>
            </div>
            ${this.renderImpersonation()}
            <slot></slot>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-nav-buttons": NavigationButtons;
    }
}
