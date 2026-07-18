import { AKElement } from "#elements/Base";
import Styles from "#elements/Expand.css";
import { type SlottedTemplateResult, type Spread } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";
import { customElement, property } from "lit/decorators.js";

import PFExpandableSection from "@patternfly/patternfly/components/ExpandableSection/expandable-section.css";

export interface IExpand {
    expanded?: boolean;
    textOpen?: string;
    textClosed?: string;
}

@customElement("ak-expand")
export class Expand extends AKElement implements IExpand {
    @property({ type: Boolean })
    public expanded = false;

    @property({ type: String, attribute: "text-open" })
    public textOpen = msg("Show less");

    @property({ type: String, attribute: "text-closed" })
    public textClosed = msg("Show more");

    static styles = [PFExpandableSection, Styles];

    render() {
        return html`<div
            class="pf-c-expandable-section pf-m-display-lg pf-m-indented ${this.expanded
                ? "pf-m-expanded"
                : ""}"
        >
            <button
                type="button"
                class="pf-c-expandable-section__toggle"
                aria-expanded=${this.expanded ? "true" : "false"}
                aria-controls="expandable-content"
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
            <div
                id="expandable-content"
                class="pf-c-expandable-section__content"
                ?hidden=${!this.expanded}
            >
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
