import { css, CSSResult, html, LitElement, property, TemplateResult } from "lit-element";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";

import "../elements/router/RouterOutlet";
import "../elements/messages/MessageContainer";
import "../elements/notifications/NotificationDrawer";
import "../elements/Banner";
import "../elements/sidebar/Sidebar";
import { until } from "lit-html/directives/until";
import { me } from "../api/Users";
import { t } from "@lingui/macro";
import { EVENT_NOTIFICATION_TOGGLE, EVENT_SIDEBAR_TOGGLE, VERSION } from "../constants";
import { AdminApi } from "authentik-api";
import { DEFAULT_CONFIG } from "../api/Config";
import { ROUTES } from "../routes_admin";

export abstract class Interface extends LitElement {
    @property({type: Boolean})
    sidebarOpen = true;

    @property({type: Boolean})
    notificationOpen = false;

    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFButton, PFDrawer, css`
            .pf-c-page__main, .pf-c-drawer__content, .pf-c-page__drawer {
                z-index: auto !important;
            }
        `];
    }

    constructor() {
        super();
        this.sidebarOpen = window.innerWidth >= 1280;
        window.addEventListener("resize", () => {
            this.sidebarOpen = window.innerWidth >= 1280;
        });
        window.addEventListener(EVENT_SIDEBAR_TOGGLE, () => {
            this.sidebarOpen = !this.sidebarOpen;
        });
        window.addEventListener(EVENT_NOTIFICATION_TOGGLE, () => {
            this.notificationOpen = !this.notificationOpen;
        });
    }

    renderSidebarItems(): TemplateResult {
        return html``;
    }

    render(): TemplateResult {
        return html`
            ${until(new AdminApi(DEFAULT_CONFIG).adminVersionRetrieve().then(version => {
                if (version.versionCurrent !== VERSION) {
                    return html`<ak-banner>
                        ${t`A newer version of the frontend is available.`}
                        <button @click=${() => { window.location.reload(true); }}>
                            ${t`Reload`}
                        </button>
                    </ak-banner>`;
                }
                return html``;
            }))}
            ${until(me().then((u) => {
                if (u.original) {
                    return html`<ak-banner>
                        ${t`You're currently impersonating ${u.user.username}.`}
                        <a href=${`/-/impersonation/end/?back=${window.location.pathname}%23${window.location.hash}`}>
                            ${t`Stop impersonation`}
                        </a>
                    </ak-banner>`;
                }
                return html``;
            }))}
            <div class="pf-c-page">
                <ak-sidebar class="pf-c-page__sidebar ${this.sidebarOpen ? "pf-m-expanded" : "pf-m-collapsed"}">
                    ${this.renderSidebarItems()}
                </ak-sidebar>
                <div class="pf-c-page__drawer">
                    <div class="pf-c-drawer ${this.notificationOpen ? "pf-m-expanded" : "pf-m-collapsed"}">
                        <div class="pf-c-drawer__main">
                            <div class="pf-c-drawer__content">
                                <div class="pf-c-drawer__body">
                                    <main class="pf-c-page__main">
                                        <ak-router-outlet .routes=${ROUTES} role="main" class="pf-c-page__main" tabindex="-1" id="main-content" defaultUrl="/overview">
                                        </ak-router-outlet>
                                    </main>
                                </div>
                            </div>
                            <ak-notification-drawer class="pf-c-drawer__panel pf-m-width-33">
                            </ak-notification-drawer>
                        </div>
                    </div>
                </div>
            </div>`;
    }

}
