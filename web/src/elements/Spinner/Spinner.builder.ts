import "#elements/ak-spinner";
import type { SpinnerSize } from "./Spinner.component";

import { type ElementRest } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

export type SpinnerProps = ElementRest & {
    size?: SpinnerSize;
    inline?: boolean;
};

/**
 * @returns {TemplateResult} A Lit template result containing the configured ak-spinner element
 * @summary Helper function to create a Spinner component programmatically
 *
 * @see {@link Spinner} - The underlying web component
 */
export function akSpinner(options: SpinnerProps = {}) {
    const { size, inline, ...rest } = options;

    return html`<ak-spinner
        ${spread(rest)}
        size=${ifDefined(size)}
        ?inline=${inline}
    ></ak-spinner>`;
}
