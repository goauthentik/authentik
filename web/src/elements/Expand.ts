import { AKElement } from "@goauthentik/elements/Base";

import { msg } from "@lit/localize";
import { css, html } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFExpandableSection from "@patternfly/patternfly/components/ExpandableSection/expandable-section.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface IExpand {
    expanded?: boolean;
    textOpen?: string;
    textClosed?: string;
}
/**
 * @class Expand
 * @element ak-expand
 *
 * An `ak-expand` is used to hide cluttering details that a user may wish to reveal, such as the raw
 * details of an alert or event.
 *
 * slot - The contents to be hidden or displayed.
 */
@customElement("ak-expand")
export class Expand extends AKElement {
    /**
     * The state of the expanded content
     *
     * @attr
     */
    @property({ type: Boolean, reflect: true })
    expanded = false;

    /**
     * The text to display next to the open/close control when the accordion is closed.
     *
     * @attr
     */
    @property()
    textOpen = msg("Show less");

    /**
     * The text to display next to the open/close control when the accordion is .
     *
     * @attr
     */
    @property()
    textClosed = msg("Show more");

    static get styles() {
        return [
            PFBase,
            PFExpandableSection,
            css`
                .pf-c-expandable-section.pf-m-display-lg {
                    background-color: var(--pf-global--BackgroundColor--100);
                }
            `,
        ];
    }

    render() {
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

declare global {
    interface HTMLElementTagNameMap {
        "ak-expand": Expand;
    }
}
