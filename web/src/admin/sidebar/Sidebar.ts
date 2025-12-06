import "#admin/sidebar/SidebarVersion";

import { AKElement } from "#elements/Base";

import Styles from "#admin/sidebar/Sidebar.css";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

@customElement("ak-sidebar")
export class Sidebar extends AKElement {
    static styles: CSSResult[] = [
        // ---
        PFPage,
        PFNav,
        Styles,
    ];

    @property({ type: Boolean })
    hidden = false;

    render(): TemplateResult {
        return html`<div part="nav" class="pf-c-nav" role="presentation">
            <ul
                id="global-nav"
                ?hidden=${this.hidden}
                aria-label=${msg("Global navigation")}
                role="navigation"
                class="pf-c-nav__list"
                part="list"
            >
                <slot></slot>
            </ul>
            <ak-sidebar-version
                exportparts="trigger:about-dialog-trigger, button-content:about-dialog-button-content, product-name, product-version"
            ></ak-sidebar-version>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sidebar": Sidebar;
    }
}
