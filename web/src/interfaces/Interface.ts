import { gettext } from "django";
import { html, LitElement, property, TemplateResult } from "lit-element";
import { SidebarItem } from "../elements/sidebar/Sidebar";

import "../elements/router/RouterOutlet";
import "../elements/messages/MessageContainer";
import "../elements/sidebar/SidebarHamburger";
import "../elements/notifications/NotificationDrawer";

export abstract class Interface extends LitElement {
    @property({type: Boolean})
    sidebarOpen = true;

    @property({type: Boolean})
    notificationOpen = false;

    abstract get sidebar(): SidebarItem[];

    createRenderRoot(): ShadowRoot | Element {
        return this;
    }

    constructor() {
        super();
        this.sidebarOpen = window.outerWidth >= 1280;
        window.addEventListener("resize", () => {
            this.sidebarOpen = window.outerWidth >= 1280;
        });
        window.addEventListener("ak-sidebar-toggle", () => {
            this.sidebarOpen = !this.sidebarOpen;
        });
        window.addEventListener("ak-notification-toggle", () => {
            this.notificationOpen = !this.notificationOpen;
        });
    }

    render(): TemplateResult {
        return html`<ak-message-container></ak-message-container>
            <div class="pf-c-page">
                <a class="pf-c-skip-to-content pf-c-button pf-m-primary" href="#main-content">${gettext("Skip to content")}</a>
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
