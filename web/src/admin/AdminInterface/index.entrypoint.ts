import "#admin/AdminInterface/AboutModal";
import "#elements/ak-locale-context/ak-locale-context";
import "#elements/banner/EnterpriseStatusBanner";
import "#elements/banner/VersionBanner";
import "#elements/messages/MessageContainer";
import "#elements/notifications/APIDrawer";
import "#elements/notifications/NotificationDrawer";
import "#elements/router/RouterOutlet";
import "#elements/sidebar/Sidebar";
import "#elements/sidebar/SidebarItem";

import {
    AdminSidebarEnterpriseEntries,
    AdminSidebarEntries,
    renderSidebarItems,
} from "./AdminSidebar.js";

import { EVENT_API_DRAWER_TOGGLE, EVENT_NOTIFICATION_DRAWER_TOGGLE } from "#common/constants";
import { configureSentry } from "#common/sentry/index";
import { me } from "#common/users";
import { WebsocketClient } from "#common/ws";

import { AuthenticatedInterface } from "#elements/AuthenticatedInterface";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";

import { SidebarToggleEventDetail } from "#components/ak-page-header";

import type { AboutModal } from "#admin/AdminInterface/AboutModal";
import { ROUTES } from "#admin/Routes";

import { CapabilitiesEnum, SessionUser, UiThemeEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { css, CSSResult, html, nothing, TemplateResult } from "lit";
import { customElement, eventOptions, property, query } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload/client");
}

@customElement("ak-interface-admin")
export class AdminInterface extends WithCapabilitiesConfig(AuthenticatedInterface) {
    //#region Properties

    @property({ type: Boolean })
    public notificationDrawerOpen = getURLParam("notificationDrawerOpen", false);

    @property({ type: Boolean })
    public apiDrawerOpen = getURLParam("apiDrawerOpen", false);

    @property({ type: Object, attribute: false })
    public user?: SessionUser;

    @query("ak-about-modal")
    public aboutModal?: AboutModal;

    @property({ type: Boolean, reflect: true })
    public sidebarOpen = false;

    @eventOptions({ passive: true })
    protected sidebarListener(event: CustomEvent<SidebarToggleEventDetail>) {
        this.sidebarOpen = !!event.detail.open;
    }

    #sidebarMatcher: MediaQueryList;
    #sidebarMediaQueryListener = (event: MediaQueryListEvent) => {
        this.sidebarOpen = event.matches;
    };

    //#endregion

    //#region Styles

    static styles: CSSResult[] = [
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

    //#endregion

    //#region Lifecycle

    constructor() {
        configureSentry(true);

        super();

        WebsocketClient.connect();

        this.#sidebarMatcher = window.matchMedia("(min-width: 1200px)");
        this.sidebarOpen = this.#sidebarMatcher.matches;
    }

    public connectedCallback() {
        super.connectedCallback();

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

        this.#sidebarMatcher.addEventListener("change", this.#sidebarMediaQueryListener, {
            passive: true,
        });
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();
        this.#sidebarMatcher.removeEventListener("change", this.#sidebarMediaQueryListener);

        WebsocketClient.close();
    }

    async firstUpdated(): Promise<void> {
        me().then((session) => {
            this.user = session;

            const canAccessAdmin =
                this.user.user.isSuperuser ||
                // TODO: somehow add `access_admin_interface` to the API schema
                this.user.user.systemPermissions.includes("access_admin_interface");

            if (!canAccessAdmin && this.user.user.pk > 0) {
                window.location.assign("/if/user/");
            }
        });
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
            <ak-skip-to-content></ak-skip-to-content>
            <div class="pf-c-page">
                <ak-page-navbar ?open=${this.sidebarOpen} @sidebar-toggle=${this.sidebarListener}>
                    <ak-version-banner></ak-version-banner>
                    <ak-enterprise-status interface="admin"></ak-enterprise-status>
                </ak-page-navbar>

                <ak-sidebar ?hidden=${!this.sidebarOpen} class="${classMap(sidebarClasses)}">
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
                                    <div class="pf-c-page__main">
                                        <ak-router-outlet
                                            role="main"
                                            aria-label="${msg("Main content")}"
                                            class="pf-c-page__main"
                                            tabindex="-1"
                                            id="main-content"
                                            defaultUrl="/administration/overview"
                                            .routes=${ROUTES}
                                        >
                                        </ak-router-outlet>
                                    </div>
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
