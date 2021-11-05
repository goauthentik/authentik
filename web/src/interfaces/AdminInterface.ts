import { t } from "@lingui/macro";

import { CSSResult, LitElement, TemplateResult, css, html } from "lit";
import { customElement, property } from "lit/decorators.js";
import { until } from "lit/directives/until.js";

import AKGlobal from "../authentik.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AdminApi, Version } from "@goauthentik/api";

import { DEFAULT_CONFIG } from "../api/Config";
import { me } from "../api/Users";
import { WebsocketClient } from "../common/ws";
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
    EVENT_SIDEBAR_TOGGLE,
    VERSION,
} from "../constants";
import "../elements/messages/MessageContainer";
import "../elements/messages/MessageContainer";
import "../elements/notifications/NotificationDrawer";
import { ID_REGEX, SLUG_REGEX, UUID_REGEX } from "../elements/router/Route";
import "../elements/router/RouterOutlet";
import "../elements/sidebar/Sidebar";
import "../elements/sidebar/SidebarItem";
import { ROUTES } from "../routesAdmin";
import "./locale";

@customElement("ak-interface-admin")
export class AdminInterface extends LitElement {
    @property({ type: Boolean })
    sidebarOpen = true;

    @property({ type: Boolean })
    notificationOpen = false;

    @property({ type: Boolean })
    apiDrawerOpen = false;

    ws: WebsocketClient;

    private version: Promise<Version>;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFButton,
            PFDrawer,
            AKGlobal,
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
                @media (prefers-color-scheme: dark) {
                    /* Global page background colour */
                    .pf-c-page {
                        --pf-c-page--BackgroundColor: var(--ak-dark-background);
                    }
                }
            `,
        ];
    }

    constructor() {
        super();
        this.ws = new WebsocketClient();
        this.sidebarOpen = window.innerWidth >= 1280;
        window.addEventListener("resize", () => {
            this.sidebarOpen = window.innerWidth >= 1280;
        });
        window.addEventListener(EVENT_SIDEBAR_TOGGLE, () => {
            this.sidebarOpen = !this.sidebarOpen;
        });
        window.addEventListener(EVENT_NOTIFICATION_DRAWER_TOGGLE, () => {
            this.notificationOpen = !this.notificationOpen;
        });
        window.addEventListener(EVENT_API_DRAWER_TOGGLE, () => {
            this.apiDrawerOpen = !this.apiDrawerOpen;
        });
        this.version = new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve();
    }

    render(): TemplateResult {
        return html` <div class="pf-c-page">
            <ak-sidebar
                class="pf-c-page__sidebar ${this.sidebarOpen ? "pf-m-expanded" : "pf-m-collapsed"}"
            >
                ${this.renderSidebarItems()}
            </ak-sidebar>
            <div class="pf-c-page__drawer">
                <div
                    class="pf-c-drawer ${this.notificationOpen || this.apiDrawerOpen
                        ? "pf-m-expanded"
                        : "pf-m-collapsed"}"
                >
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
                            class="pf-c-drawer__panel pf-m-width-33 ${this.notificationOpen
                                ? ""
                                : "display-none"}"
                            ?hidden=${!this.notificationOpen}
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

    renderSidebarItems(): TemplateResult {
        me().then((u) => {
            if (!u.user.isSuperuser) {
                window.location.assign("/if/user");
            }
        });
        return html`
            ${until(
                this.version.then((version) => {
                    if (version.versionCurrent !== VERSION) {
                        return html`<ak-sidebar-item ?highlight=${true}>
                            <span slot="label"
                                >${t`A newer version of the frontend is available.`}</span
                            >
                        </ak-sidebar-item>`;
                    }
                    return html``;
                }),
            )}
            ${until(
                me().then((u) => {
                    if (u.original) {
                        return html`<ak-sidebar-item
                            ?highlight=${true}
                            ?isAbsoluteLink=${true}
                            path=${`/-/impersonation/end/?back=${window.location.pathname}%23${window.location.hash}`}
                        >
                            <span slot="label"
                                >${t`You're currently impersonating ${u.user.username}. Click to stop.`}</span
                            >
                        </ak-sidebar-item>`;
                    }
                    return html``;
                }),
            )}
            <ak-sidebar-item path="/if/user/" ?isAbsoluteLink=${true} ?highlight=${true}>
                <span slot="label">${t`User interface`}</span>
            </ak-sidebar-item>
            <ak-sidebar-item path="/administration/overview">
                <span slot="label">${t`Overview`}</span>
            </ak-sidebar-item>
            <ak-sidebar-item path="/administration/system-tasks">
                <span slot="label">${t`System Tasks`}</span>
            </ak-sidebar-item>
            <ak-sidebar-item>
                <span slot="label">${t`Resources`}</span>
                <ak-sidebar-item
                    path="/core/applications"
                    .activeWhen=${[`^/core/applications/(?<slug>${SLUG_REGEX})$`]}
                >
                    <span slot="label">${t`Applications`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item
                    path="/core/sources"
                    .activeWhen=${[`^/core/sources/(?<slug>${SLUG_REGEX})$`]}
                >
                    <span slot="label">${t`Sources`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item
                    path="/core/providers"
                    .activeWhen=${[`^/core/providers/(?<id>${ID_REGEX})$`]}
                >
                    <span slot="label">${t`Providers`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/tenants">
                    <span slot="label">${t`Tenants`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item>
                <span slot="label">${t`Outposts`}</span>
                <ak-sidebar-item path="/outpost/outposts">
                    <span slot="label">${t`Outposts`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/outpost/integrations">
                    <span slot="label">${t`Integrations`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item>
                <span slot="label">${t`Events`}</span>
                <ak-sidebar-item
                    path="/events/log"
                    .activeWhen=${[`^/events/log/(?<id>${UUID_REGEX})$`]}
                >
                    <span slot="label">${t`Logs`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/events/rules">
                    <span slot="label">${t`Notification Rules`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/events/transports">
                    <span slot="label">${t`Notification Transports`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item>
                <span slot="label">${t`Customisation`}</span>
                <ak-sidebar-item path="/policy/policies">
                    <span slot="label">${t`Policies`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/policy/reputation/ip">
                    <span slot="label">${t`Reputation policy - IPs`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/policy/reputation/user">
                    <span slot="label">${t`Reputation policy - Users`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/property-mappings">
                    <span slot="label">${t`Property Mappings`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item>
                <span slot="label">${t`Flows`}</span>
                <ak-sidebar-item
                    path="/flow/flows"
                    .activeWhen=${[`^/flow/flows/(?<slug>${SLUG_REGEX})$`]}
                >
                    <span slot="label">${t`Flows`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/flow/stages">
                    <span slot="label">${t`Stages`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/flow/stages/prompts">
                    <span slot="label">${t`Prompts`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/flow/stages/invitations">
                    <span slot="label">${t`Invitations`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item>
                <span slot="label">${t`Identity & Cryptography`}</span>
                <ak-sidebar-item
                    path="/identity/users"
                    .activeWhen=${[`^/identity/users/(?<id>${ID_REGEX})$`]}
                >
                    <span slot="label">${t`Users`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/identity/groups">
                    <span slot="label">${t`Groups`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/crypto/certificates">
                    <span slot="label">${t`Certificates`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/tokens">
                    <span slot="label">${t`Tokens & App passwords`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
        `;
    }
}
