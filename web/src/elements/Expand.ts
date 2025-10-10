import { AKElement } from "#elements/Base";
import { type SlottedTemplateResult, type Spread } from "#elements/types";

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
    @property({ type: Boolean, reflect: true })
    public expanded = false;

    @property({ type: String, attribute: "text-open" })
    public textOpen = msg("Show less");

    @property({ type: String, attribute: "text-closed" })
    public textClosed = msg("Show more");

    static styles = [
        PFBase,
        PFExpandableSection,
        css`
            .pf-c-expandable-section {
                display: grid;
                grid-template-columns: 1fr;
                font-family: var(--pf-global--FontFamily--heading--sans-serif);
                --pf-c-expandable-section__toggle-icon--Transition: 100ms ease-in 0s;
            }

            .pf-c-expandable-section__toggle {
                user-select: none;

                &:hover {
                    text-decoration: underline;
                }
            }

            .attachment-target {
                position: relative;
            }
        `,
    ];

    render() {
        return html`<div
            class="pf-c-expandable-section pf-m-display-lg pf-m-indented ${this.expanded
                ? "pf-m-expanded"
                : ""}"
            part="container"
        >
            <button
                type="button"
                part="toggle"
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

            <div class="attachment-target" part="attachment-target" ?hidden=${!this.expanded}>
                ${this.hasSlotted(null)
                    ? html`<div
                          id="expandable-content"
                          part="content"
                          class="pf-c-expandable-section__content"
                      >
                          <slot></slot>
                      </div>`
                    : nothing}
                <slot name="actions"></slot>
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
