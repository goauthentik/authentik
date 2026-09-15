/**
 * @file Implementation code for the ExpansionToggle
 */

import Styles from "./ExpansionToggle.styles";

import { AKElement } from "#elements/Base";
import { type ElementRest } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { spread } from "@open-wc/lit-helpers";

import { msg } from "@lit/localize";
import { html, nothing, TemplateResult } from "lit";
import { property, query, state } from "lit/decorators.js";

const toggleState = (o: boolean) => (o ? "open" : "closed");

const LABEL_ID = "expansion-toggle-label";

const ANGLE_RIGHT = html`<svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 256 512"
    aria-hidden="true"
>
    <path
        d="M224.3 273l-136 136c-9.4 9.4-24.6 9.4-33.9 0l-22.6-22.6c-9.4-9.4-9.4-24.6 0-33.9l96.4-96.4-96.4-96.4c-9.4-9.4-9.4-24.6 0-33.9L54.3 103c9.4-9.4 24.6-9.4 33.9 0l136 136c9.5 9.4 9.5 24.6.1 34z"
    />
</svg>`;

const DEFAULT_OPEN_LABEL = msg("Open", {
    id: "expansion-toggle.aria-label.open",
    desc: "Accessible name for an icon-only disclosure toggle that is currently closed.",
});

const DEFAULT_CLOSE_LABEL = msg("Close", {
    id: "expansion-toggle.aria-label.close",
    desc: "Accessible name for an icon-only disclosure toggle that is currently open.",
});

export class ExpansionToggle extends AKElement {
    static readonly styles = [Styles];

    @property({ type: Boolean, reflect: true })
    expanded = false;

    @property({ attribute: "close-label" })
    closeLabel = DEFAULT_CLOSE_LABEL;

    @property({ attribute: "open-label" })
    openLabel = DEFAULT_OPEN_LABEL;

    @property({ attribute: false })
    public controls?: Element;

    @query("button")
    button!: HTMLButtonElement;

    protected override updated() {
        const button = this.renderRoot.querySelector("button");
        if (!button || !("ariaControlsElements" in button)) return;
        button.ariaControlsElements = this.controls ? [this.controls] : null;
    }

    @state()
    protected labelled = false;

    public override connectedCallback() {
        super.connectedCallback();
        this.labelled = this.querySelector(':scope > [slot="label"]') !== null;
    }

    #onLabelSlotChange = (ev: Event) => {
        this.labelled = (ev.target as HTMLSlotElement).assignedElements().length > 0;
    };

    protected onClick() {
        const oldState = toggleState(this.expanded);
        this.expanded = !this.expanded;
        this.dispatchEvent(
            new ToggleEvent("toggle", {
                oldState,
                newState: toggleState(this.expanded),
                composed: true,
                bubbles: true,
            }),
        );
    }

    protected renderToggle(labelled: boolean) {
        const { expanded } = this;

        return html` <button
            type="button"
            part="button"
            aria-labelledby=${ifPresent(labelled, LABEL_ID)}
            aria-label=${ifPresent(!labelled, expanded ? this.closeLabel : this.openLabel)}
            aria-expanded=${expanded ? "true" : "false"}
        >
            <div part="icon-container">${ANGLE_RIGHT}</div>
        </button>`;
    }

    render() {
        return html` <div part="expansion-toggle" @click=${this.onClick}>
            <div part="toggle">${this.renderToggle(this.labelled)}</div>
            <div id=${LABEL_ID} part="label" ?hidden=${!this.labelled}>
                <slot name="label" @slotchange=${this.#onLabelSlotChange}></slot>
            </div>
        </div>`;
    }
}

export type ExpansionToggleProps = ElementRest & {
    reversed?: boolean;
    expanded?: boolean;
    content?: string | TemplateResult | null;
};

/**
 * @summary Helper function to create an ExpansionToggle component programmatically
 *
 * @returns {TemplateResult} A Lit template result containing the configured ak-expansion-toggle element
 *
 * @see {@link ExpansionToggle} - The underlying web component
 */
export function akExpansionToggle(options: ExpansionToggleProps = {}) {
    const { reversed, expanded, content, ...rest } = options;

    return html`
        <ak-expansion-toggle ${spread(rest)} ?reversed=${reversed} ?expanded=${expanded}
            >${content ? html`<span slot="label">${content}</span>` : nothing}
        </ak-expansion-toggle>
    `;
}
