import "#components/ak-nav-buttons";
import "#elements/ak-locale-context/ak-locale-context";
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
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
    EVENT_WS_MESSAGE,
} from "#common/constants";
import { globalAK } from "#common/global";
import { configureSentry } from "#common/sentry/index";
import { DefaultBrand, getConfigForUser, UIConfig } from "#common/ui/config";
import { me } from "#common/users";
import { WebsocketClient } from "#common/ws";

import { AuthenticatedInterface } from "#elements/AuthenticatedInterface";
import { AKElement } from "#elements/Base";
import { WithBrandConfig } from "#elements/mixins/branding";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";
import { themeImage } from "#elements/utils/images";

import { ROUTES } from "#user/Routes";

import { EventsApi, SessionUser } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFAvatar from "@patternfly/patternfly/components/Avatar/avatar.css";
import PFBrand from "@patternfly/patternfly/components/Brand/brand.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFDropdown from "@patternfly/patternfly/components/Dropdown/dropdown.css";
import PFNotificationBadge from "@patternfly/patternfly/components/NotificationBadge/notification-badge.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFDisplay from "@patternfly/patternfly/utilities/Display/display.css";

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload/client");
}

const customStyles = css`
    .pf-c-page__main,
    .pf-c-drawer__content,
    .pf-c-page__drawer {
        z-index: auto !important;
        background-color: transparent !important;
    }
    .pf-c-page__header {
        background-color: transparent !important;
        box-shadow: none !important;
        color: black !important;
    }
    :host([theme="light"]) .pf-c-button.pf-m-secondary {
        color: var(--ak-global--Color--100) !important;
    }
    .pf-c-page {
        background-color: transparent;
    }
    .display-none {
        display: none;
    }
    .pf-c-brand {
        min-height: 32px;
        height: 32px;
    }
    .has-notifications {
        color: #2b9af3;
    }
    .background-wrapper {
        height: 100vh;
        width: 100%;
        position: fixed;
        z-index: -1;
        top: 0;
        left: 0;
        background-color: var(--pf-c-page--BackgroundColor) !important;
    }
    .background-default-slant {
        background-color: white; /*var(--ak-accent);*/
        clip-path: polygon(0 0, 100% 0, 100% 100%, 0 calc(100% - 5vw));
        height: 50vh;
    }
    :host([theme="dark"]) .background-default-slant {
        background-color: black;
    }
    ak-locale-context {
        display: flex;
        flex-direction: column;
    }
    .pf-c-drawer__main {
        min-height: calc(100vh - 76px);
        max-height: calc(100vh - 76px);
    }
`;

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
class UserInterfacePresentation extends WithBrandConfig(AKElement) {
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
        customStyles,
    ];

    @property({ type: Object })
    uiConfig!: UIConfig;

    @property({ type: Object })
    me!: SessionUser;

    @property({ type: Boolean, reflect: true })
    notificationDrawerOpen = false;

    @property({ type: Boolean, reflect: true })
    apiDrawerOpen = false;

    @property({ type: Number })
    notificationsCount = 0;

    get canAccessAdmin() {
        return (
            this.me.user.isSuperuser ||
            // TODO: somehow add `access_admin_interface` to the API schema
            this.me.user.systemPermissions.includes("access_admin_interface")
        );
    }

    get isFullyConfigured() {
        return Boolean(this.uiConfig && this.me && this.brand);
    }

    renderAdminInterfaceLink() {
        if (!this.canAccessAdmin) {
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
        // The `!` in the field definitions above only re-assure typescript and eslint that the
        // values *should* be available, not that they *are*. Thus this contract check; it asserts
        // that the contract we promised is being honored, and the rest of the code that depends on
        // `!` being truthful is not being lied to.
        if (!this.isFullyConfigured) {
            throw new Error("ak-interface-user-presentation misused; no valid values passed");
        }

        return html`<ak-locale-context>
            <ak-enterprise-status interface="user"></ak-enterprise-status>
            <div class="pf-c-page">
                <div class="background-wrapper" style="${this.uiConfig.theme.background}">
                    ${(this.uiConfig.theme.background || "") === ""
                        ? html`<div class="background-default-slant"></div>`
                        : html``}
                </div>
                <header class="pf-c-page__header">
                    <div class="pf-c-page__header-brand">
                        <a href="#/" class="pf-c-page__header-brand-link">
                            <img
                                class="pf-c-brand"
                                src="${themeImage(this.brandingLogo)}"
                                alt="${this.brandingTitle}"
                            />
                        </a>
                    </div>
                    <ak-nav-buttons .uiConfig=${this.uiConfig} .me=${this.me}
                        >${this.renderAdminInterfaceLink()}</ak-nav-buttons
                    >
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
                                    <main class="pf-c-page__main">
                                        <ak-router-outlet
                                            class="pf-l-bullseye__item pf-c-page__main"
                                            tabindex="-1"
                                            id="main-content"
                                            defaultUrl="/library"
                                            .routes=${ROUTES}
                                        >
                                        </ak-router-outlet>
                                    </main>
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
            </div>
        </ak-locale-context>`;
    }
}

//  ___         _
// | _ )_  _ __(_)_ _  ___ ______
// | _ \ || (_-< | ' \/ -_|_-<_-<
// |___/\_,_/__/_|_||_\___/__/__/
//
//
@customElement("ak-interface-user")
export class UserInterface extends WithBrandConfig(AuthenticatedInterface) {
    @property({ type: Boolean })
    notificationDrawerOpen = getURLParam("notificationDrawerOpen", false);

    @state()
    apiDrawerOpen = getURLParam("apiDrawerOpen", false);

    @state()
    notificationsCount = 0;

    @state()
    me: SessionUser | null = null;

    @state()
    uiConfig: UIConfig | null = null;

    constructor() {
        configureSentry(true);

        super();

        WebsocketClient.connect();

        this.fetchConfigurationDetails();
        this.toggleNotificationDrawer = this.toggleNotificationDrawer.bind(this);
        this.toggleApiDrawer = this.toggleApiDrawer.bind(this);
        this.fetchConfigurationDetails = this.fetchConfigurationDetails.bind(this);
    }

    async connectedCallback() {
        super.connectedCallback();

        window.addEventListener(EVENT_NOTIFICATION_DRAWER_TOGGLE, this.toggleNotificationDrawer);
        window.addEventListener(EVENT_API_DRAWER_TOGGLE, this.toggleApiDrawer);
        window.addEventListener(EVENT_WS_MESSAGE, this.fetchConfigurationDetails);
    }

    disconnectedCallback() {
        super.disconnectedCallback();

        window.removeEventListener(EVENT_NOTIFICATION_DRAWER_TOGGLE, this.toggleNotificationDrawer);
        window.removeEventListener(EVENT_API_DRAWER_TOGGLE, this.toggleApiDrawer);
        window.removeEventListener(EVENT_WS_MESSAGE, this.fetchConfigurationDetails);

        WebsocketClient.close();
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

    fetchConfigurationDetails() {
        me().then((session: SessionUser) => {
            this.me = session;
            this.uiConfig = getConfigForUser(session.user);

            new EventsApi(DEFAULT_CONFIG)
                .eventsNotificationsList({
                    seen: false,
                    ordering: "-created",
                    pageSize: 1,
                    user: this.me.user.pk,
                })
                .then((notifications) => {
                    this.notificationsCount = notifications.pagination.count;
                });
        });
    }

    render() {
        if (!this.me) {
            console.debug(`authentik/user/UserInterface: waiting for user session to be available`);

            return nothing;
        }

        if (!this.uiConfig) {
            console.debug(`authentik/user/UserInterface: waiting for UI config to be available`);

            return nothing;
        }

        return html`<ak-interface-user-presentation
            .uiConfig=${this.uiConfig}
            .me=${this.me}
            .brand=${this.brand ?? DefaultBrand}
            ?notificationDrawerOpen=${this.notificationDrawerOpen}
            ?apiDrawerOpen=${this.apiDrawerOpen}
            notificationsCount=${this.notificationsCount}
        ></ak-interface-user-presentation>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-interface-user-presentation": UserInterfacePresentation;
        "ak-interface-user": UserInterface;
    }
}
