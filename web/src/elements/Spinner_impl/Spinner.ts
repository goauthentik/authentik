/**
 * @file Implementation code for the Spinner component
 */

import styles from "./Spinner.styles";

import type { ElementRest } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { html, LitElement } from "lit";
import { property } from "lit/decorators.js";
import { ifDefined } from "lit/directives/if-defined.js";

/**
 * Spinner size variants. Prefer T-shirt sizes when possible. Because these have no behavioral
 * consequences, they're not actually used here, but we document them here for the `.builder`.
 */
export type SpinnerSize = "sm" | "md" | "lg" | "xl";

/**
 * @element ak-spinner
 *
 * A **spinner** is a visual element used to communicate that an underlying task is in progress.
 * Spinners are used with loading pages, but can also be used in buttons and smaller elements to
 * communicate on-page events.
 *
 * @summary Shows a user a "task is in progess"
 *
 * @attr {SpinnerSize} size - Size of the spinner: "sm", "md" (default), "lg", "xl"
 * @attr {string} label - Accessible label for screen readers
 * @attr {boolean} inline - Whether spinner uses inline sizing (1em)
 *
 * @usage
 * The spinner also supports an `inline` boolean attribute that sets the diameter
 * to 1em, allowing it to scale with surrounding text.
 *
 * @csspart spinner - The SVG element for the spinner container
 * @csspart circle - The SVG circle element for the actual spinning part
 *
 */
export class Spinner extends LitElement {
    static override readonly styles = [styles];

    @property()
    public label?: string;

    public override render() {
        return html`<svg
            part="spinner"
            role="progressbar"
            viewBox="0 0 100 100"
            aria-label=${ifDefined(this.label)}
        >
            <circle part="circle" cx="50" cy="50" r="45" fill="none" />
        </svg>`;
    }
}

export type SpinnerProps = ElementRest &
    Partial<Pick<Spinner, "label">> & {
        inline?: boolean;
        size?: SpinnerSize;
    };

/**
 * @summary Helper function to create a Spinner component programmatically
 *
 * @returns {TemplateResult} A Lit template result containing the configured ak-spinner element
 *
 * @see {@link Spinner} - The underlying web component
 */
export function akSpinner(options: SpinnerProps = { inline: false }) {
    const { size, label, inline, ...rest } = options;

    return html`<ak-spinner
        ${spread(rest)}
        size=${ifDefined(size)}
        label=${ifDefined(label)}
        ?inline=${!!inline}
    ></ak-spinner>`;
}
