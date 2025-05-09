import "@goauthentik/admin/AdminInterface/AboutModal";
import type { AboutModal } from "@goauthentik/admin/AdminInterface/AboutModal";
import { ROUTES } from "@goauthentik/admin/Routes";
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
    EVENT_SIDEBAR_TOGGLE,
} from "@goauthentik/common/constants";
import { setSentryPII, tryInitializeSentry } from "@goauthentik/common/sentry";
import { ServerContext } from "@goauthentik/common/server-context";
import { me } from "@goauthentik/common/users";
import { WebsocketClient } from "@goauthentik/common/ws";
import { AuthenticatedInterface } from "@goauthentik/elements/Interface";
import { WithCapabilitiesConfig } from "@goauthentik/elements/Interface/capabilitiesProvider";
import { WithLicenseSummary } from "@goauthentik/elements/Interface/licenseSummaryProvider.js";
import "@goauthentik/elements/ak-locale-context";
import "@goauthentik/elements/banner/EnterpriseStatusBanner";
import "@goauthentik/elements/banner/EnterpriseStatusBanner";
import "@goauthentik/elements/banner/VersionBanner";
import "@goauthentik/elements/banner/VersionBanner";
import "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/notifications/APIDrawer";
import "@goauthentik/elements/notifications/NotificationDrawer";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import "@goauthentik/elements/router/RouterOutlet";
import "@goauthentik/elements/sidebar/Sidebar";
import "@goauthentik/elements/sidebar/SidebarItem";

import { CSSResult, TemplateResult, css, html, nothing } from "lit";
import { customElement, property, query, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { CapabilitiesEnum, SessionUser, UiThemeEnum } from "@goauthentik/api";

import {
    AdminSidebarEnterpriseEntries,
    AdminSidebarEntries,
    renderSidebarItems,
} from "./AdminSidebar.js";

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload/client");
}

@customElement("ak-interface-admin")
export class AdminInterface extends WithCapabilitiesConfig(
    WithLicenseSummary(AuthenticatedInterface),
) {
    //#region Properties

    @property({ type: Boolean })
    notificationDrawerOpen = getURLParam("notificationDrawerOpen", false);

    @property({ type: Boolean })
    apiDrawerOpen = getURLParam("apiDrawerOpen", false);

    ws: WebsocketClient;

    @state()
    user?: SessionUser;

    @query("ak-about-modal")
    aboutModal?: AboutModal;

    @property({ type: Boolean, reflect: true })
    public sidebarOpen: boolean;

    #toggleSidebar = () => {
        this.sidebarOpen = !this.sidebarOpen;
    };

    #sidebarMatcher: MediaQueryList;
    #sidebarListener = (event: MediaQueryListEvent) => {
        this.sidebarOpen = event.matches;
    };

    //#endregion

    //#region Styles

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFButton,
            PFDrawer,
            PFNav,
            css`
                .pf-c-page__main,
                .pf-c-drawer__content,
                .pf-c-page__drawer {
                    z-index: auto !important;
                    background-color: transparent;
                }

                .display-none {
                    display: none;
                }

                .pf-c-page {
                    background-color: var(--pf-c-page--BackgroundColor) !important;
                }

                :host([theme="dark"]) {
                    /* Global page background colour */
                    .pf-c-page {
                        --pf-c-page--BackgroundColor: var(--ak-dark-background);
                    }
                }

                ak-page-navbar {
                    grid-area: header;
                }

                .ak-sidebar {
                    grid-area: nav;
                }

                .pf-c-drawer__panel {
                    z-index: var(--pf-global--ZIndex--xl);
                }
            `,
        ];
    }

    //#endregion

    //#region Lifecycle

    constructor() {
        super();
        this.ws = new WebsocketClient();

        this.#sidebarMatcher = window.matchMedia("(min-width: 1200px)");
        this.sidebarOpen = this.#sidebarMatcher.matches;
    }

    public connectedCallback() {
        super.connectedCallback();

        window.addEventListener(EVENT_SIDEBAR_TOGGLE, this.#toggleSidebar);

        window.addEventListener(EVENT_NOTIFICATION_DRAWER_TOGGLE, () => {
            this.notificationDrawerOpen = !this.notificationDrawerOpen;
            updateURLParams({
                notificationDrawerOpen: this.notificationDrawerOpen,
            });
        });

        window.addEventListener(EVENT_API_DRAWER_TOGGLE, () => {
            this.apiDrawerOpen = !this.apiDrawerOpen;
            updateURLParams({
                apiDrawerOpen: this.apiDrawerOpen,
            });
        });

        this.#sidebarMatcher.addEventListener("change", this.#sidebarListener);
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        window.removeEventListener(EVENT_SIDEBAR_TOGGLE, this.#toggleSidebar);
        this.#sidebarMatcher.removeEventListener("change", this.#sidebarListener);
    }

    async firstUpdated(): Promise<void> {
        tryInitializeSentry(ServerContext.config);
        this.user = await me();

        setSentryPII(this.user.user);

        const canAccessAdmin =
            this.user.user.isSuperuser ||
            // TODO: somehow add `access_admin_interface` to the API schema
            this.user.user.systemPermissions.includes("access_admin_interface");

        if (!canAccessAdmin && this.user.user.pk > 0) {
            console.debug(
                "authentik/admin: User does not have access to admin interface. Redirecting...",
            );

            window.location.assign("/if/user/");
        }
    }

    render(): TemplateResult {
        const sidebarClasses = {
            "pf-c-page__sidebar": true,
            "pf-m-light": this.activeTheme === UiThemeEnum.Light,
            "pf-m-expanded": this.sidebarOpen,
            "pf-m-collapsed": !this.sidebarOpen,
        };

        const drawerOpen = this.notificationDrawerOpen || this.apiDrawerOpen;

        const drawerClasses = {
            "pf-m-expanded": drawerOpen,
            "pf-m-collapsed": !drawerOpen,
        };

        return html` <ak-locale-context>
            <div class="pf-c-page">
                <ak-page-navbar>
                    <ak-version-banner></ak-version-banner>
                    <ak-enterprise-status interface="admin"></ak-enterprise-status>
                </ak-page-navbar>

                <ak-sidebar class="${classMap(sidebarClasses)}">
                    ${renderSidebarItems(AdminSidebarEntries)}
                    ${this.can(CapabilitiesEnum.IsEnterprise)
                        ? renderSidebarItems(AdminSidebarEnterpriseEntries)
                        : nothing}
                </ak-sidebar>

                <div class="pf-c-page__drawer">
                    <div class="pf-c-drawer ${classMap(drawerClasses)}">
                        <div class="pf-c-drawer__main">
                            <div class="pf-c-drawer__content">
                                <div class="pf-c-drawer__body">
                                    <main class="pf-c-page__main">
                                        <ak-router-outlet
                                            role="main"
                                            class="pf-c-page__main"
                                            tabindex="-1"
                                            id="main-content"
                                            defaultUrl="/administration/overview"
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
                            <ak-about-modal></ak-about-modal>
                        </div>
                    </div>
                </div></div
        ></ak-locale-context>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-interface-admin": AdminInterface;
    }
}
