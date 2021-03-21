import { css, CSSResult, html, LitElement, property, TemplateResult } from "lit-element";
import { SidebarItem } from "../elements/sidebar/Sidebar";
import PFBase from "@patternfly/patternfly/patternfly-base.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";
import PFSkipToContent from "@patternfly/patternfly/components/SkipToContent/skip-to-content.css";
import PFButton from "@patternfly/patternfly/components/Button/button.css";
import PFDrawer from "@patternfly/patternfly/components/Drawer/drawer.css";

import "../elements/router/RouterOutlet";
import "../elements/messages/MessageContainer";
import "../elements/sidebar/SidebarHamburger";
import "../elements/notifications/NotificationDrawer";
import "../elements/Banner";
import { until } from "lit-html/directives/until";
import { me } from "../api/Users";
import { gettext } from "django";

export abstract class Interface extends LitElement {
    @property({type: Boolean})
    sidebarOpen = true;

    @property({type: Boolean})
    notificationOpen = false;

    abstract get sidebar(): SidebarItem[];

    static get styles(): CSSResult[] {
        return [PFBase, PFPage, PFSkipToContent, PFButton, PFDrawer, css`
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
        window.addEventListener("ak-sidebar-toggle", () => {
            this.sidebarOpen = !this.sidebarOpen;
        });
        window.addEventListener("ak-notification-toggle", () => {
            this.notificationOpen = !this.notificationOpen;
        });
    }

    render(): TemplateResult {
        return html`
            ${until(me().then((u) => {
                if (u.original) {
                    return html`<ak-banner>
                        ${gettext(`You're currently impersonating ${u.user.username}.`)}
                        <a href=${`/-/impersonation/end/?back=${window.location.pathname}%23${window.location.hash}`}>
                            ${gettext("Stop impersonation")}
                        </a>
                    </ak-banner>`;
                }
                return html``;
            }))}
            <div class="pf-c-page">
                <ak-sidebar-hamburger>
                </ak-sidebar-hamburger>
                <ak-sidebar class="pf-c-page__sidebar ${this.sidebarOpen ? "pf-m-expanded" : "pf-m-collapsed"}" .items=${this.sidebar}>
                </ak-sidebar>
                <div class="pf-c-page__drawer">
                    <div class="pf-c-drawer ${this.notificationOpen ? "pf-m-expanded" : "pf-m-collapsed"}">
                        <div class="pf-c-drawer__main">
                            <div class="pf-c-drawer__content">
                                <div class="pf-c-drawer__body">
                                    <main class="pf-c-page__main">
                                        <ak-router-outlet role="main" class="pf-c-page__main" tabindex="-1" id="main-content" defaultUrl="/library">
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
