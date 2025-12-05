import "#admin/AdminInterface/AboutModal";
import "#elements/banner/EnterpriseStatusBanner";
import "#elements/banner/VersionBanner";
import "#elements/messages/MessageContainer";
import "#elements/notifications/APIDrawer";
import "#elements/notifications/NotificationDrawer";
import "#elements/router/RouterOutlet";
import "#admin/sidebar/Sidebar";
import "#admin/sidebar/SidebarItem";

import {
    createAdminSidebarEnterpriseEntries,
    createAdminSidebarEntries,
    renderSidebarItems,
} from "./AdminSidebar.js";

import { isAPIResultReady } from "#common/api/responses";
import { EVENT_API_DRAWER_TOGGLE, EVENT_NOTIFICATION_DRAWER_TOGGLE } from "#common/constants";
import { configureSentry } from "#common/sentry/index";
import { isGuest } from "#common/users";
import { WebsocketClient } from "#common/ws";

import { AuthenticatedInterface } from "#elements/AuthenticatedInterface";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { canAccessAdmin, WithSession } from "#elements/mixins/session";
import { getURLParam, updateURLParams } from "#elements/router/RouteMatch";

import { PageNavMenuToggle } from "#components/ak-page-navbar";

import type { AboutModal } from "#admin/AdminInterface/AboutModal";
import Styles from "#admin/AdminInterface/index.entrypoint.css";
import { ROUTES } from "#admin/Routes";

import { CapabilitiesEnum } from "@goauthentik/api";

import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, property, query } from "lit/decorators.js";
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
export class AdminInterface extends WithCapabilitiesConfig(WithSession(AuthenticatedInterface)) {
    //#region Properties

    @property({ type: Boolean })
    public notificationDrawerOpen = getURLParam("notificationDrawerOpen", false);

    @property({ type: Boolean })
    public apiDrawerOpen = getURLParam("apiDrawerOpen", false);

    @query("ak-about-modal")
    public aboutModal?: AboutModal;

    @property({ type: Boolean, reflect: true })
    public sidebarOpen = false;

    #onPageNavMenuEvent = (event: PageNavMenuToggle) => {
        this.sidebarOpen = event.open;
    };

    #sidebarMatcher: MediaQueryList;
    #sidebarMediaQueryListener = (event: MediaQueryListEvent) => {
        this.sidebarOpen = event.matches;
    };

    //#endregion

    //#region Styles

    static styles: CSSResult[] = [
        // ---
        PFBase,
        PFPage,
        PFButton,
        PFDrawer,
        PFNav,
        Styles,
    ];

    //#endregion

    //#region Lifecycle

    constructor() {
        configureSentry();

        super();

        WebsocketClient.connect();

        this.#sidebarMatcher = window.matchMedia("(min-width: 1200px)");
        this.sidebarOpen = this.#sidebarMatcher.matches;
        this.addEventListener(PageNavMenuToggle.eventName, this.#onPageNavMenuEvent, {
            passive: true,
        });
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

    public override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("session") && isAPIResultReady(this.session)) {
            if (!isGuest(this.session.user) && !canAccessAdmin(this.session.user)) {
                window.location.assign("/if/user/");
            }
        }
    }

    render(): TemplateResult {
        if (!isAPIResultReady(this.session) || !canAccessAdmin(this.session.user)) {
            return html`<slot></slot>`;
        }

        const sidebarClasses = {
            "pf-c-page__sidebar": true,
            "pf-m-expanded": this.sidebarOpen,
            "pf-m-collapsed": !this.sidebarOpen,
        };

        const drawerOpen = this.notificationDrawerOpen || this.apiDrawerOpen;

        const drawerClasses = {
            "pf-m-expanded": drawerOpen,
            "pf-m-collapsed": !drawerOpen,
        };

        return html`<div class="pf-c-page">
            <ak-page-navbar ?open=${this.sidebarOpen}>
                <ak-version-banner></ak-version-banner>
                <ak-enterprise-status interface="admin"></ak-enterprise-status>
            </ak-page-navbar>

            <ak-sidebar ?hidden=${!this.sidebarOpen} class="${classMap(sidebarClasses)}"
                >${renderSidebarItems(createAdminSidebarEntries())}
                ${this.can(CapabilitiesEnum.IsEnterprise)
                    ? renderSidebarItems(createAdminSidebarEnterpriseEntries())
                    : nothing}
            </ak-sidebar>

            <div class="pf-c-page__drawer">
                <div class="pf-c-drawer ${classMap(drawerClasses)}">
                    <div class="pf-c-drawer__main">
                        <div class="pf-c-drawer__content">
                            <div class="pf-c-drawer__body">
                                <ak-router-outlet
                                    role="presentation"
                                    class="pf-c-page__main"
                                    tabindex="-1"
                                    id="main-content"
                                    defaultUrl="/administration/overview"
                                    .routes=${ROUTES}
                                >
                                </ak-router-outlet>
                            </div>
                        </div>
                        <ak-notification-drawer
                            class="pf-c-drawer__panel pf-m-width-33 ${this.notificationDrawerOpen
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
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-interface-admin": AdminInterface;
    }
}
