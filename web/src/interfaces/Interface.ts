import { gettext } from "django";
import { CSSResult, html, LitElement, TemplateResult } from "lit-element";
import { COMMON_STYLES } from "../common/styles";
import { SidebarItem } from "../elements/sidebar/Sidebar";

// @customElement("pb-interface")
export abstract class Interface extends LitElement {

    abstract get sidebar(): SidebarItem[];

    static get styles(): CSSResult[] {
        return COMMON_STYLES;
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
