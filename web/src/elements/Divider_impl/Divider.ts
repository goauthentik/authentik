/**
 * @file Implementation code for the Divider component
 */

import styles from "./Divider.styles";

import { classList } from "#elements/directives/class-list";
import { type ElementRest } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { html, LitElement, type TemplateResult } from "lit";
import { state } from "lit/decorators/state.js";
import { ifDefined } from "lit/directives/if-defined.js";

// These are documented here because they are used by the builder as type constraints. They have
// only visual consequences so there are no properties matching them in the component's Typescript
// code.

export const dividerVariant = ["default", "strong", "subtle"] as const;
export type DividerVariant = (typeof dividerVariant)[number];

export const dividerOrientation = ["horizontal", "vertical"] as const;
export type DividerOrientation = (typeof dividerOrientation)[number];

/**
 * @element ak-divider
 * @summary A visual divider that creates thematic breaks or separation between content sections
 *
 * @attr {string} variant - Visual style variant: "default", "strong", "subtle"
 * @attr {string} orientation - Layout orientation: "horizontal", "vertical"
 *
 * @slot - Optional content to display in the middle of the divider line
 *
 * @csspart divider - The main container element for the divider
 * @csspart line - The line elements (before and after content if content exists)
 * @csspart start - The line element before content (when content is present)
 * @csspart end - The line element after content (when content is present)
 * @csspart content - The wrapper around the slotted content
 *
 * See the `Divider.root.css` file in this folder for the CSS Custom Properties that
 * control the appearance of this component.
 */

export class Divider extends LitElement {
    static readonly styles = [styles];

    @state()
    private hasContent = false;

    private onSlotChange = (ev: Event) => {
        const nodes = (ev.target as HTMLSlotElement).assignedNodes({ flatten: true });
        this.hasContent = nodes.some(
            (n) =>
                n.nodeType === Node.ELEMENT_NODE ||
                (n.nodeType === Node.TEXT_NODE && (n.textContent ?? "").trim().length > 0),
        );
    };

    render() {
        const contentClass = classList([this.hasContent && "has-content"]);
        return html`<div part="divider">
            <span part="line start"></span>
            <span part="content" class=${contentClass}
                ><slot @slotchange=${this.onSlotChange}></slot
            ></span>
            <span part="line end"></span>
        </div> `;
    }

    updated() {
        if (this.hasContent) {
            this.removeAttribute("role");
        } else {
            this.setAttribute("role", "separator");
        }
    }
}

export type DividerProps = ElementRest & {
    variant?: DividerVariant;
    orientation?: DividerOrientation;
    content?: string | TemplateResult;
};

/**
 * @summary Helper function to create a Divider component programmatically
 *
 * @returns {TemplateResult} A Lit template result containing the configured ak-divider element
 *
 * @see {@link Divider} - The underlying web component
 */
export function akDivider(options: DividerProps = {}) {
    const { variant, orientation, content, ...rest } = options;

    // Handle string content by wrapping in a span
    const message = typeof content === "string" ? html`<span>${content.trim()}</span>` : content;

    return html`
        <ak-divider
            ${spread(rest)}
            variant=${ifDefined(variant)}
            orientation=${ifDefined(orientation)}
            >${message}</ak-divider
        >
    `;
}
