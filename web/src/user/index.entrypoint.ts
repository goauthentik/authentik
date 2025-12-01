import "#components/ak-nav-buttons";
import "#elements/banner/EnterpriseStatusBanner";
import "#elements/buttons/ActionButton/ak-action-button";
import "#elements/messages/MessageContainer";
import "#elements/notifications/APIDrawer";
import "#elements/notifications/NotificationDrawer";
import "#elements/router/RouterOutlet";
import "#elements/sidebar/Sidebar";
import "#elements/sidebar/SidebarItem";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { EVENT_API_DRAWER_TOGGLE, EVENT_NOTIFICATION_DRAWER_TOGGLE } from "#common/constants";
import { globalAK } from "#common/global";
import { configureSentry } from "#common/sentry/index";
import { isGuest } from "#common/users";
import { WebsocketClient } from "#common/ws";

import { AuthenticatedInterface } from "#elements/AuthenticatedInterface";
import { AKElement } from "#elements/Base";
import { WithBrandConfig } from "#elements/mixins/branding";
import { canAccessAdmin, WithSession } from "#elements/mixins/session";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";
import { ifPresent } from "#elements/utils/attributes";
import { themeImage } from "#elements/utils/images";

import Styles from "#user/index.entrypoint.css";
import { ROUTES } from "#user/Routes";

import { EventsApi } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { html, nothing, PropertyValues } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFBrand from "@patternfly/patternfly/components/Brand/brand.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationBadge from "@patternfly/patternfly/components/NotificationBadge/notification-badge.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload/client");
}

//  ___                     _        _   _
// | _ \_ _ ___ ___ ___ _ _| |_ __ _| |_(_)___ _ _
// |  _/ '_/ -_|_-</ -_) ' \  _/ _` |  _| / _ \ ' \
// |_| |_| \___/__/\___|_||_\__\__,_|\__|_\___/_||_|
//

// Despite the length of the render() method and its accessories, this top-level Interface does
// surprisingly little. It has been broken into two parts: the business logic at the bottom, and the
// rendering code at the top, which is wholly independent of APIs and Interfaces.

// Because this is not exported, and because it's invoked as a web component, neither TSC or ESLint
// trusts that we actually used it. Hence the double ignore below:

@customElement("ak-interface-user-presentation")
// @ts-ignore
class UserInterfacePresentation extends WithBrandConfig(WithSession(AKElement)) {
    static styles = [
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

    @property({ type: Boolean, reflect: true })
    notificationDrawerOpen = false;

    @property({ type: Boolean, reflect: true })
    apiDrawerOpen = false;

    @property({ type: Number })
    notificationsCount = 0;

    renderAdminInterfaceLink() {
        if (!canAccessAdmin(this.currentUser)) {
            return nothing;
        }

        return html`<a
                class="pf-c-button pf-m-secondary pf-m-small pf-u-display-none pf-u-display-block-on-md"
                href="${globalAK().api.base}if/admin/"
                slot="extra"
            >
                ${msg("Admin interface")}
            </a>
            <a
                class="pf-c-button pf-m-secondary pf-m-small pf-u-display-none-on-md pf-u-display-block"
                href="${globalAK().api.base}if/admin/"
                slot="extra"
            >
                ${msg("Admin")}
            </a>`;
    }

    render() {
        const { currentUser } = this;

        if (!currentUser) {
            console.debug(`authentik/user/UserInterface: waiting for user session to be available`);

            return html`<slot></slot>`;
        }

        if (isGuest(currentUser)) {
            // TODO: There might be a hidden feature here.
            // Allowing guest users to see some parts of the interface?
            // Maybe redirect to a flow?

            return html`<slot></slot>`;
        }

        const backgroundStyles = this.uiConfig.theme.background;

        return html`<ak-enterprise-status interface="user"></ak-enterprise-status>
            <div class="pf-c-page">
                <div class="background-wrapper" style=${ifPresent(backgroundStyles)}>
                    ${!backgroundStyles
                        ? html`<div class="background-default-slant"></div>`
                        : nothing}
                </div>
                <header class="pf-c-page__header">
                    <div class="pf-c-page__header-brand">
                        <a href="#/" class="pf-c-page__header-brand-link">
                            <img
                                class="pf-c-brand"
                                src="${themeImage(this.brandingLogo, this.activeTheme)}"
                                alt="${this.brandingTitle}"
                            />
                        </a>
                    </div>
                    <ak-nav-buttons>${this.renderAdminInterfaceLink()}</ak-nav-buttons>
                </header>
                <div class="pf-c-page__drawer">
                    <div
                        class="pf-c-drawer ${this.notificationDrawerOpen || this.apiDrawerOpen
                            ? "pf-m-expanded"
                            : "pf-m-collapsed"}"
                    >
                        <div class="pf-c-drawer__main">
                            <div class="pf-c-drawer__content">
                                <div class="pf-c-drawer__body">
                                    <ak-router-outlet
                                        class="pf-l-bullseye__item pf-c-page__main"
                                        tabindex="-1"
                                        id="main-content"
                                        defaultUrl="/library"
                                        .routes=${ROUTES}
                                    >
                                    </ak-router-outlet>
                                </div>
                            </div>
                            <ak-notification-drawer
                                class="pf-c-drawer__panel pf-m-width-33 ${this
                                    .notificationDrawerOpen
                                    ? ""
                                    : "display-none"}"
                                ?hidden=${!this.notificationDrawerOpen}
                            ></ak-notification-drawer>
                            <ak-api-drawer
                                class="pf-c-drawer__panel pf-m-width-33 ${this.apiDrawerOpen
                                    ? ""
                                    : "display-none"}"
                                ?hidden=${!this.apiDrawerOpen}
                            ></ak-api-drawer>
                        </div>
                    </div>
                </div>
            </div>`;
    }
}

//  ___         _
// | _ )_  _ __(_)_ _  ___ ______
// | _ \ || (_-< | ' \/ -_|_-<_-<
// |___/\_,_/__/_|_||_\___/__/__/
//
//
@customElement("ak-interface-user")
export class UserInterface extends WithBrandConfig(WithSession(AuthenticatedInterface)) {
    public static shadowRootOptions = { ...AKElement.shadowRootOptions, delegatesFocus: true };

    public override tabIndex = -1;

    @property({ type: Boolean })
    notificationDrawerOpen = getURLParam("notificationDrawerOpen", false);

    @state()
    apiDrawerOpen = getURLParam("apiDrawerOpen", false);

    @state()
    notificationsCount = 0;

    constructor() {
        configureSentry();

        super();

        WebsocketClient.connect();

        this.toggleNotificationDrawer = this.toggleNotificationDrawer.bind(this);
        this.toggleApiDrawer = this.toggleApiDrawer.bind(this);
    }

    async connectedCallback() {
        super.connectedCallback();

        window.addEventListener(EVENT_NOTIFICATION_DRAWER_TOGGLE, this.toggleNotificationDrawer);
        window.addEventListener(EVENT_API_DRAWER_TOGGLE, this.toggleApiDrawer);
    }

    disconnectedCallback() {
        super.disconnectedCallback();

        window.removeEventListener(EVENT_NOTIFICATION_DRAWER_TOGGLE, this.toggleNotificationDrawer);
        window.removeEventListener(EVENT_API_DRAWER_TOGGLE, this.toggleApiDrawer);

        WebsocketClient.close();
    }

    public updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("session")) {
            this.refreshNotifications();
        }
    }

    protected refreshNotifications(): Promise<void> {
        const { currentUser } = this;

        if (!currentUser || isGuest(currentUser)) {
            return Promise.resolve();
        }

        return new EventsApi(DEFAULT_CONFIG)
            .eventsNotificationsList({
                seen: false,
                ordering: "-created",
                pageSize: 1,
                user: currentUser.pk,
            })
            .then((notifications) => {
                this.notificationsCount = notifications.pagination.count;
            });
    }

    toggleNotificationDrawer() {
        this.notificationDrawerOpen = !this.notificationDrawerOpen;
        updateURLParams({
            notificationDrawerOpen: this.notificationDrawerOpen,
        });
    }

    toggleApiDrawer() {
        this.apiDrawerOpen = !this.apiDrawerOpen;
        updateURLParams({
            apiDrawerOpen: this.apiDrawerOpen,
        });
    }

    render() {
        const { currentUser } = this;

        if (!currentUser || isGuest(currentUser)) {
            console.debug(`authentik/user/UserInterface: waiting for user session to be available`);

            return html`<slot></slot>`;
        }

        return html`<ak-interface-user-presentation
            ?notificationDrawerOpen=${this.notificationDrawerOpen}
            ?apiDrawerOpen=${this.apiDrawerOpen}
            notificationsCount=${this.notificationsCount}
        >
            <slot name="placeholder"></slot>
        </ak-interface-user-presentation>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-interface-user-presentation": UserInterfacePresentation;
        "ak-interface-user": UserInterface;
    }
}
