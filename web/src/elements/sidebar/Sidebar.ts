import PFNav from "@patternfly/patternfly/components/Nav/nav.css";
import PFPage from "@patternfly/patternfly/components/Page/page.css";

import { AKElement } from "#elements/Base";
import Styles from "#elements/sidebar/Sidebar.css";

import { SlotController } from "@patternfly/pfe-core/controllers/slot-controller.js";

import { msg } from "@lit/localize";
import { CSSResult, html, TemplateResult } from "lit";
import { customElement, property } from "lit/decorators.js";

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

    protected slots = new SlotController(this, {
        slots: [null, "footer"],
    });

    render(): TemplateResult {
        return html`<div part="nav" class="pf-c-nav" role="presentation">
            <ul
                id="global-nav"
                ?hidden=${this.hidden}
                aria-label=${msg("Global navigation")}
                role="navigation"
                class="pf-c-nav__list ak-m-thin-scrollbar ak-m-scroll-shadows"
                part="list"
            >
                <slot></slot>
            </ul>
            <div ?hidden=${!this.slots.hasSlotted("footer")} part="footer">
                <slot name="footer"></slot>
            </div>
        </div>`;
    }
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-sidebar": Sidebar;
    }
}
