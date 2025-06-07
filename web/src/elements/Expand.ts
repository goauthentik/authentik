import { AKElement } from "@goauthentik/elements/Base";
import { type SlottedTemplateResult, type Spread } from "@goauthentik/elements/types";
import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { css, html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFExpandableSection from "@patternfly/patternfly/components/ExpandableSection/expandable-section.css";
import PFBase from "@patternfly/patternfly/patternfly-base.css";

export interface IExpand {
    expanded?: boolean;
    textOpen?: string;
    textClosed?: string;
}

@customElement("ak-expand")
export class Expand extends AKElement implements IExpand {
    @property({ type: Boolean })
    expanded = false;

    @property({ type: String, attribute: "text-open" })
    textOpen = msg("Show less");

    @property({ type: String, attribute: "text-closed" })
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

export function akExpand(properties: IExpand, content: SlottedTemplateResult = nothing) {
    const message = typeof content === "string" ? html`<span>${content}</span>` : content;
    return html`<ak-expand ${spread(properties as Spread)}>${message}</ak-expand>`;
}

declare global {
    interface HTMLElementTagNameMap {
        "ak-expand": Expand;
    }
}
