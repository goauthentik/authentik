import "#admin/AdminInterface/AboutModal";
import "#elements/banner/EnterpriseStatusBanner";
import "#elements/banner/VersionBanner";
import "#elements/messages/MessageContainer";
import "#elements/router/RouterOutlet";
import "#elements/sidebar/Sidebar";
import "#elements/sidebar/SidebarItem";

import {
    createAdminSidebarEnterpriseEntries,
    createAdminSidebarEntries,
    createFilteredAdminSidebarEnterpriseEntries,
    createFilteredAdminSidebarEntries,
    renderSidebarItems,
} from "./AdminSidebar.js";
import type { UIPermissions } from "./uiPermissions.js";

import { DEFAULT_CONFIG } from "#common/api/config";
import { isAPIResultReady } from "#common/api/responses";
import { configureSentry } from "#common/sentry/index";
import { isGuest } from "#common/users";
import { WebsocketClient } from "#common/ws/WebSocketClient";

import { AuthenticatedInterface } from "#elements/AuthenticatedInterface";
import { listen } from "#elements/decorators/listen";
import { WithCapabilitiesConfig } from "#elements/mixins/capabilities";
import { WithNotifications } from "#elements/mixins/notifications";
import { canAccessAdmin, WithSession } from "#elements/mixins/session";
import { AKDrawerChangeEvent } from "#elements/notifications/events";
import {
    DrawerState,
    persistDrawerParams,
    readDrawerParams,
    renderNotificationDrawerPanel,
} from "#elements/notifications/utils";

import type { AboutModal } from "#admin/AdminInterface/AboutModal";
import Styles from "#admin/AdminInterface/index.entrypoint.css";
import { ROUTES } from "#admin/Routes";

import { CapabilitiesEnum } from "@goauthentik/api";

import { msg } from "@lit/localize";
import { CSSResult, html, nothing, PropertyValues, TemplateResult } from "lit";
import { customElement, eventOptions, property, query, state } from "lit/decorators.js";
import { classMap } from "lit/directives/class-map.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

if (process.env.NODE_ENV === "development") {
    await import("@goauthentik/esbuild-plugin-live-reload/client");
}

@customElement("ak-interface-admin")
export class AdminInterface extends WithCapabilitiesConfig(
    WithNotifications(WithSession(AuthenticatedInterface)),
) {
    //#region Styles

    public static readonly styles: CSSResult[] = [PFPage, PFButton, PFDrawer, PFNav, Styles];

    //#endregion

    //#region Properties

    @query("ak-about-modal")
    public aboutModal?: AboutModal;

    @property({ type: Boolean, reflect: true, attribute: "sidebar" })
    public sidebarOpen = false;

    @state()
    protected uiPermissions: UIPermissions | null = null;

    //#endregion

    //#region Public Methods

    public toggleSidebar = () => {
        this.sidebarOpen = !this.sidebarOpen;
    };

    //#endregion

    //#region Lifecycle

    #sidebarMatcher: MediaQueryList;
    #sidebarMediaQueryListener = (event: MediaQueryListEvent) => {
        this.sidebarOpen = event.matches;
    };

    @eventOptions({ passive: true })
    protected routeChangeListener() {
        this.sidebarOpen = this.#sidebarMatcher.matches;
    }

    @state()
    protected drawer: DrawerState = readDrawerParams();

    @listen(AKDrawerChangeEvent)
    protected drawerListener = (event: AKDrawerChangeEvent) => {
        this.drawer = event.drawer;
        persistDrawerParams(event.drawer);
    };

    constructor() {
        configureSentry();

        super();

        WebsocketClient.connect();

        this.#sidebarMatcher = window.matchMedia("(width >= 1200px)");
        this.sidebarOpen = this.#sidebarMatcher.matches;
    }

    public connectedCallback() {
        super.connectedCallback();

        this.#sidebarMatcher.addEventListener("change", this.#sidebarMediaQueryListener, {
            passive: true,
        });

        this.fetchUIPermissions();
    }

    public disconnectedCallback(): void {
        super.disconnectedCallback();

        this.#sidebarMatcher.removeEventListener("change", this.#sidebarMediaQueryListener);

        WebsocketClient.close();
    }

    protected async fetchUIPermissions() {
        try {
            const response = await fetch(`${DEFAULT_CONFIG.basePath}/admin/ui_permissions/`, {
                headers: {
                    "Content-Type": "application/json",
                },
            });
            if (response.ok) {
                this.uiPermissions = await response.json();
            }
        } catch (error) {
            console.error("Failed to fetch UI permissions:", error);
            this.uiPermissions = null;
        }
    }

    public override updated(changedProperties: PropertyValues<this>): void {
        super.updated(changedProperties);

        if (changedProperties.has("session") && isAPIResultReady(this.session)) {
            if (!isGuest(this.session.user) && !canAccessAdmin(this.session.user)) {
                window.location.assign("/if/user/");
            }
            if (changedProperties.get("session") !== this.session) {
                this.fetchUIPermissions();
            }
        }
    }

    //#endregion

    //#region Rendering

    protected override render(): TemplateResult {
        if (!isAPIResultReady(this.session) || !canAccessAdmin(this.session.user)) {
            return html`<slot></slot>`;
        }

        const sidebarClasses = {
            "pf-c-page__sidebar": true,
            "pf-m-expanded": this.sidebarOpen,
            "pf-m-collapsed": !this.sidebarOpen,
        };

        const openDrawerCount = (this.drawer.notifications ? 1 : 0) + (this.drawer.api ? 1 : 0);
        const drawerClasses = {
            "pf-m-expanded": openDrawerCount !== 0,
            "pf-m-collapsed": openDrawerCount === 0,
        };

        const sidebarEntries = this.uiPermissions
            ? createFilteredAdminSidebarEntries(this.uiPermissions)
            : createAdminSidebarEntries();

        const enterpriseEntries = this.uiPermissions
            ? createFilteredAdminSidebarEnterpriseEntries(this.uiPermissions)
            : createAdminSidebarEnterpriseEntries();

        return html`<div class="pf-c-page">
            <ak-page-navbar>
                <button
                    slot="toggle"
                    aria-controls="global-nav"
                    class="pf-c-button pf-m-plain"
                    @click=${this.toggleSidebar}
                    aria-label=${this.sidebarOpen
                        ? msg("Collapse navigation")
                        : msg("Expand navigation")}
                    aria-expanded=${this.sidebarOpen ? "true" : "false"}
                >
                    <i aria-hidden="true" class="fas fa-bars"></i>
                </button>

                <ak-version-banner></ak-version-banner>
                <ak-enterprise-status interface="admin"></ak-enterprise-status>
            </ak-page-navbar>

            <ak-sidebar ?hidden=${!this.sidebarOpen} class="${classMap(sidebarClasses)}"
                >${renderSidebarItems(sidebarEntries)}
                ${this.can(CapabilitiesEnum.IsEnterprise)
                    ? renderSidebarItems(enterpriseEntries)
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
                                    @ak-route-change=${this.routeChangeListener}
                                >
                                </ak-router-outlet>
                            </div>
                        </div>
                        ${renderNotificationDrawerPanel(this.drawer)}
                        <ak-about-modal></ak-about-modal>
                    </div>
                </div>

                <div
                    class="pf-c-page__sidebar-backdrop"
                    aria-label=${this.sidebarOpen ? msg("Close sidebar") : msg("Open sidebar")}
                    @click=${this.toggleSidebar}
                    role="button"
                    tabindex="0"
                ></div>
            </div>
        </div>`;
    }

    //#endregion
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-interface-admin": AdminInterface;
    }
}
