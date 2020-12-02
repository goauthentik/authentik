import { gettext } from "django";
import { html, LitElement, TemplateResult } from "lit-element";
import { SidebarItem } from "../elements/sidebar/Sidebar";

import "../elements/Messages";
import "../pages/router/RouterOutlet";

export abstract class Interface extends LitElement {

    abstract get sidebar(): SidebarItem[];

    createRenderRoot(): ShadowRoot | Element {
        return this;
    }

    render(): TemplateResult {
        return html`<pb-messages></pb-messages>
            <div class="pf-c-page">
                <a class="pf-c-skip-to-content pf-c-button pf-m-primary" href="#main-content">${gettext("Skip to content")}</a>
                <pb-sidebar class="pf-c-page__sidebar" .items=${this.sidebar}>
                </pb-sidebar>
                <main class="pf-c-page__main">
                    <pb-router-outlet role="main" class="pf-c-page__main" tabindex="-1" id="main-content" defaultUrl="/library/">
                    </pb-router-outlet>
                </main>
            </div>`;
    }

}
