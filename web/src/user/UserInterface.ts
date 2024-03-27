import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
    EVENT_WS_MESSAGE,
} from "@goauthentik/common/constants";
import { configureSentry } from "@goauthentik/common/sentry";
import { UIConfig, UserDisplay } from "@goauthentik/common/ui/config";
import { me } from "@goauthentik/common/users";
import { WebsocketClient } from "@goauthentik/common/ws";
import { AKElement } from "@goauthentik/elements/Base";
import { EnterpriseAwareInterface } from "@goauthentik/elements/Interface";
import "@goauthentik/elements/ak-locale-context";
import "@goauthentik/elements/buttons/ActionButton";
import "@goauthentik/elements/enterprise/EnterpriseStatusBanner";
import "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/notifications/APIDrawer";
import "@goauthentik/elements/notifications/NotificationDrawer";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import "@goauthentik/elements/router/RouterOutlet";
import "@goauthentik/elements/sidebar/Sidebar";
import { DefaultBrand } from "@goauthentik/elements/sidebar/SidebarBrand";
import "@goauthentik/elements/sidebar/SidebarItem";
import { ROUTES } from "@goauthentik/user/Routes";
import "@goauthentik/user/user-settings/details/UserSettingsFlowExecutor";
import "@patternfly/elements/pf-tooltip/pf-tooltip.js";
import { match } from "ts-pattern";

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

import { CoreApi, CurrentBrand, EventsApi, SessionUser } from "@goauthentik/api";

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
    :host([theme="dark"]) .pf-c-page__header {
        color: var(--ak-dark-foreground) !important;
    }
    :host([theme="light"]) .pf-c-page__header-tools-item .fas,
    :host([theme="light"]) .pf-c-notification-badge__count,
    :host([theme="light"]) .pf-c-page__header-tools-group .pf-c-button {
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
// eslint-disable-next-line @typescript-eslint/no-unused-vars
class UserInterfacePresentation extends AKElement {
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
            customStyles,
        ];
    }

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

    @property({ type: Object })
    brand!: CurrentBrand;

    get userDisplayName() {
        return match<UserDisplay, string>(this.uiConfig.navbar.userDisplay)
            .with(UserDisplay.username, () => this.me.user.username)
            .with(UserDisplay.name, () => this.me.user.name)
            .with(UserDisplay.email, () => this.me.user.email || "")
            .otherwise(() => this.me.user.username);
    }

    get canAccessAdmin() {
        return (
            this.me.user.isSuperuser ||
            // TODO: somehow add `access_admin_interface` to the API schema
            this.me.user.systemPermissions.includes("access_admin_interface")
        );
    }

    get isFullyConfigured() {
        return !!(this.uiConfig && this.me && this.brand);
    }

    render() {
        // The `!` in the field definitions above only re-assure typescript and eslint that the
        // values *should* be available, not that they *are*. Thus this contract check; it asserts
        // that the contract we promised is being honored, and the rest of the code that depends on
        // `!` being truthful is not being lied to.
        if (!this.isFullyConfigured) {
            throw new Error("ak-interface-user-presentation misused; no valid values passed");
        }

        return html` <ak-locale-context>
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
                                src="${this.brand.brandingLogo}"
                                alt="${this.brand.brandingTitle}"
                            />
                        </a>
                    </div>
                    <div class="pf-c-page__header-tools">
                        <div class="pf-c-page__header-tools-group">
                            ${this.renderApiDrawerTrigger()}
                            <!-- -->
                            ${this.renderNotificationDrawerTrigger()}
                            <!-- -->
                            ${this.renderSettings()}
                            <div class="pf-c-page__header-tools-item">
                                <a
                                    href="/flows/-/default/invalidation/"
                                    class="pf-c-button pf-m-plain"
                                >
                                    <pf-tooltip position="top" content=${msg("Sign out")}>
                                        <i class="fas fa-sign-out-alt" aria-hidden="true"></i>
                                    </pf-tooltip>
                                </a>
                            </div>
                            ${this.renderAdminInterfaceLink()}
                        </div>
                        ${this.renderImpersonation()}
                        <div class="pf-c-page__header-tools-group">
                            <div
                                class="pf-c-page__header-tools-item pf-m-hidden pf-m-visible-on-md"
                            >
                                ${this.userDisplayName}
                            </div>
                        </div>
                        <img
                            class="pf-c-avatar"
                            src=${this.me.user.avatar}
                            alt="${msg("Avatar image")}"
                        />
                    </div>
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
                                            role="main"
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

    renderApiDrawerTrigger() {
        if (!this.uiConfig.enabledFeatures.apiDrawer) {
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
        if (!this.uiConfig.enabledFeatures.notificationDrawer) {
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
        if (!this.uiConfig.enabledFeatures.settings) {
            return nothing;
        }

        return html` <div class="pf-c-page__header-tools-item">
            <a class="pf-c-button pf-m-plain" type="button" href="#/settings">
                <pf-tooltip position="top" content=${msg("Settings")}>
                    <i class="fas fa-cog" aria-hidden="true"></i>
                </pf-tooltip>
            </a>
        </div>`;
    }

    renderAdminInterfaceLink() {
        if (!this.canAccessAdmin) {
            return nothing;
        }

        return html`<a
            class="pf-c-button pf-m-secondary pf-m-small pf-u-display-none pf-u-display-block-on-md"
            href="/if/admin/"
        >
            ${msg("Admin interface")}
        </a>`;
    }

    renderImpersonation() {
        if (!this.me.original) {
            return nothing;
        }

        const onClick = () => {
            return new CoreApi(DEFAULT_CONFIG).coreUsersImpersonateEndRetrieve().then(() => {
                window.location.reload();
            });
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
}

//  ___         _
// | _ )_  _ __(_)_ _  ___ ______
// | _ \ || (_-< | ' \/ -_|_-<_-<
// |___/\_,_/__/_|_||_\___/__/__/
//
//
@customElement("ak-interface-user")
export class UserInterface extends EnterpriseAwareInterface {
    @property({ type: Boolean })
    notificationDrawerOpen = getURLParam("notificationDrawerOpen", false);

    @state()
    apiDrawerOpen = getURLParam("apiDrawerOpen", false);

    ws: WebsocketClient;

    @state()
    notificationsCount = 0;

    @state()
    me?: SessionUser;

    constructor() {
        super();
        this.ws = new WebsocketClient();
        this.fetchConfigurationDetails();
        configureSentry(true);
        this.toggleNotificationDrawer = this.toggleNotificationDrawer.bind(this);
        this.toggleApiDrawer = this.toggleApiDrawer.bind(this);
        this.fetchConfigurationDetails = this.fetchConfigurationDetails.bind(this);
    }

    connectedCallback() {
        super.connectedCallback();
        window.addEventListener(EVENT_NOTIFICATION_DRAWER_TOGGLE, this.toggleNotificationDrawer);
        window.addEventListener(EVENT_API_DRAWER_TOGGLE, this.toggleApiDrawer);
        window.addEventListener(EVENT_WS_MESSAGE, this.fetchConfigurationDetails);
    }

    disconnectedCallback() {
        window.removeEventListener(EVENT_NOTIFICATION_DRAWER_TOGGLE, this.toggleNotificationDrawer);
        window.removeEventListener(EVENT_API_DRAWER_TOGGLE, this.toggleApiDrawer);
        window.removeEventListener(EVENT_WS_MESSAGE, this.fetchConfigurationDetails);
        super.disconnectedCallback();
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
        me().then((me: SessionUser) => {
            this.me = me;
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

    get isFullyConfigured() {
        return !!(this.uiConfig && this.me);
    }

    render() {
        if (!this.isFullyConfigured) {
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
