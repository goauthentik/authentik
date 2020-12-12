import { gettext } from "django";
import { html, LitElement, TemplateResult } from "lit-element";
import { SidebarItem } from "../elements/sidebar/Sidebar";

import "../elements/router/RouterOutlet";
import "../elements/messages/MessageContainer";

export abstract class Interface extends LitElement {

    abstract get sidebar(): SidebarItem[];

    createRenderRoot(): ShadowRoot | Element {
        return this;
    }

    render(): TemplateResult {
        return html`<ak-message-container></ak-message-container>
            <div class="pf-c-page">
                <a class="pf-c-skip-to-content pf-c-button pf-m-primary" href="#main-content">${gettext("Skip to content")}</a>
                <ak-sidebar class="pf-c-page__sidebar" .items=${this.sidebar}>
                </ak-sidebar>
                <main class="pf-c-page__main">
                    <ak-router-outlet role="main" class="pf-c-page__main" tabindex="-1" id="main-content" defaultUrl="/library/">
                    </ak-router-outlet>
                </main>
            </div>`;
    }

}
