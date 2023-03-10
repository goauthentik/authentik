import { ROUTES } from "@goauthentik/admin/Routes";
import { DEFAULT_CONFIG } from "@goauthentik/common/api/config";
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
    EVENT_SIDEBAR_TOGGLE,
    VERSION,
} from "@goauthentik/common/constants";
import { autoDetectLanguage } from "@goauthentik/common/ui/locale";
import { me } from "@goauthentik/common/users";
import { WebsocketClient } from "@goauthentik/common/ws";
import { Interface } from "@goauthentik/elements/Base";
import "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/messages/MessageContainer";
import "@goauthentik/elements/notifications/APIDrawer";
import "@goauthentik/elements/notifications/NotificationDrawer";
import { ID_REGEX, SLUG_REGEX, UUID_REGEX } from "@goauthentik/elements/router/Route";
import { getURLParam, updateURLParams } from "@goauthentik/elements/router/RouteMatch";
import "@goauthentik/elements/router/RouterOutlet";
import "@goauthentik/elements/sidebar/Sidebar";
import "@goauthentik/elements/sidebar/SidebarItem";

import { t } from "@lingui/macro";

import { CSSResult, TemplateResult, css, html } from "lit";
import { customElement, property, state } from "lit/decorators.js";

import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

import { AdminApi, SessionUser, Version } from "@goauthentik/api";

autoDetectLanguage();

@customElement("ak-interface-admin")
export class AdminInterface extends Interface {
    @property({ type: Boolean })
    sidebarOpen = true;

    @property({ type: Boolean })
    notificationDrawerOpen = getURLParam("notificationDrawerOpen", false);

    @property({ type: Boolean })
    apiDrawerOpen = getURLParam("apiDrawerOpen", false);

    ws: WebsocketClient;

    @state()
    version?: Version;

    @state()
    user?: SessionUser;

    static get styles(): CSSResult[] {
        return [
            PFBase,
            PFPage,
            PFButton,
            PFDrawer,
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
                /* Global page background colour */
                :host([theme="dark"]) .pf-c-page {
                    --pf-c-page--BackgroundColor: var(--ak-dark-background);
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
    }

    async firstUpdated(): Promise<void> {
        this.version = await new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve();
        this.user = await me();
        if (!this.user.user.isSuperuser && this.user.user.pk > 0) {
            window.location.assign("/if/user");
        }
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
                    </div>
                </div>
            </div>
        </div>`;
    }

    renderSidebarItems(): TemplateResult {
        return html`
            ${this.version && this.version.versionCurrent !== VERSION
                ? html`
                      <ak-sidebar-item ?highlight=${true}>
                          <span slot="label"
                              >${t`A newer version of the frontend is available.`}</span
                          >
                      </ak-sidebar-item>
                  `
                : html``}
            ${this.user?.original
                ? html`<ak-sidebar-item
                      ?highlight=${true}
                      ?isAbsoluteLink=${true}
                      path=${`/-/impersonation/end/?back=${encodeURIComponent(
                          `${window.location.pathname}#${window.location.hash}`,
                      )}`}
                  >
                      <span slot="label"
                          >${t`You're currently impersonating ${this.user.user.username}. Click to stop.`}</span
                      >
                  </ak-sidebar-item>`
                : html``}
            <ak-sidebar-item path="/if/user/" ?isAbsoluteLink=${true} ?highlight=${true}>
                <span slot="label">${t`User interface`}</span>
            </ak-sidebar-item>
            <ak-sidebar-item .expanded=${true}>
                <span slot="label">${t`Dashboards`}</span>
                <ak-sidebar-item path="/administration/overview">
                    <span slot="label">${t`Overview`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/administration/dashboard/users">
                    <span slot="label">${t`Users`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/administration/system-tasks">
                    <span slot="label">${t`System Tasks`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item>
                <span slot="label">${t`Applications`}</span>
                <ak-sidebar-item
                    path="/core/applications"
                    .activeWhen=${[`^/core/applications/(?<slug>${SLUG_REGEX})$`]}
                >
                    <span slot="label">${t`Applications`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item
                    path="/core/providers"
                    .activeWhen=${[`^/core/providers/(?<id>${ID_REGEX})$`]}
                >
                    <span slot="label">${t`Providers`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/outpost/outposts">
                    <span slot="label">${t`Outposts`}</span>
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
                <ak-sidebar-item path="/core/property-mappings">
                    <span slot="label">${t`Property Mappings`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/blueprints/instances">
                    <span slot="label">${t`Blueprints`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/policy/reputation">
                    <span slot="label">${t`Reputation scores`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item>
                <span slot="label">${t`Flows & Stages`}</span>
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
            </ak-sidebar-item>
            <ak-sidebar-item>
                <span slot="label">${t`Directory`}</span>
                <ak-sidebar-item
                    path=${`/identity/users;${encodeURIComponent(
                        JSON.stringify({
                            path: "users",
                        }),
                    )}`}
                    .activeWhen=${[`^/identity/users/(?<id>${ID_REGEX})$`]}
                >
                    <span slot="label">${t`Users`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item
                    path="/identity/groups"
                    .activeWhen=${[`^/identity/groups/(?<id>${UUID_REGEX})$`]}
                >
                    <span slot="label">${t`Groups`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item
                    path="/core/sources"
                    .activeWhen=${[`^/core/sources/(?<slug>${SLUG_REGEX})$`]}
                >
                    <span slot="label">${t`Federation & Social login`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/core/tokens">
                    <span slot="label">${t`Tokens & App passwords`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/flow/stages/invitations">
                    <span slot="label">${t`Invitations`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
            <ak-sidebar-item>
                <span slot="label">${t`System`}</span>
                <ak-sidebar-item path="/core/tenants">
                    <span slot="label">${t`Tenants`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/crypto/certificates">
                    <span slot="label">${t`Certificates`}</span>
                </ak-sidebar-item>
                <ak-sidebar-item path="/outpost/integrations">
                    <span slot="label">${t`Outpost Integrations`}</span>
                </ak-sidebar-item>
            </ak-sidebar-item>
        `;
    }
}
