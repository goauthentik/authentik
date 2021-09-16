import "../elements/messages/MessageContainer";
import {
    css,
    CSSResult,
    customElement,
    html,
    LitElement,
    property,
    TemplateResult,
} from "lit-element";
import { me } from "../api/Users";
import "./locale";
import "../elements/sidebar/SidebarItem";
import { t } from "@lingui/macro";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";
import AKGlobal from "../authentik.css";

import "../elements/router/RouterOutlet";
import "../elements/messages/MessageContainer";
import "../elements/notifications/NotificationDrawer";
import "../elements/sidebar/Sidebar";
import { until } from "lit-html/directives/until";
import {
    EVENT_API_DRAWER_TOGGLE,
    EVENT_NOTIFICATION_DRAWER_TOGGLE,
    EVENT_SIDEBAR_TOGGLE,
    VERSION,
} from "../constants";
import { AdminApi, Version } from "@goauthentik/api";
import { DEFAULT_CONFIG } from "../api/Config";
import { WebsocketClient } from "../common/ws";
import { ROUTES } from "../routesUser";

@customElement("ak-interface-user")
export class UserInterface extends LitElement {
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
                }
                .display-none {
                    display: none;
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
                                        defaultUrl="/library"
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
            <ak-sidebar-item path="/if/admin" ?isAbsoluteLink=${true} ?highlight=${true}>
                <span slot="label">${t`Go to admin interface`}</span>
            </ak-sidebar-item>
            <ak-sidebar-item path="/library">
                <span slot="label">${t`Library`}</span>
            </ak-sidebar-item>
        `;
    }
}
