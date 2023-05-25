import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { CSSResult, TemplateResult, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFExpandableSection from "@patternfly/patternfly/components/ExpandableSection/expandable-section.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

@customElement("ak-expand")
export class Expand extends AKElement {
    @property({ type: Boolean })
    expanded = false;

    @property()
    textOpen = msg("Show less");

    @property()
    textClosed = msg("Show more");

    static get styles(): CSSResult[] {
        return [PFBase, PFExpandableSection];
    }

    render(): TemplateResult {
        return html`<div
            class="pf-c-expandable-section pf-m-display-lg pf-m-indented ${this.expanded
                ? "pf-m-expanded"
                : ""}"
        >
            <button
                type="button"
                class="pf-c-expandable-section__toggle"
                aria-expanded="${this.expanded}"
                @click=${() => {
                    this.expanded = !this.expanded;
                }}
            >
                <span class="pf-c-expandable-section__toggle-icon">
                    <i class="fas fa-angle-right" aria-hidden="true"></i>
                </span>
                <span class="pf-c-expandable-section__toggle-text"
                    >${this.expanded ? this.textOpen : this.textClosed}</span
                >
            </button>
            <div class="pf-c-expandable-section__content" ?hidden=${!this.expanded}>
                <slot></slot>
            </div>
        </div>`;
    }
}
