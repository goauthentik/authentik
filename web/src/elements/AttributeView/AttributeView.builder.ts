import { type ElementRest } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";
import { ifDefined } from "lit-html/directives/if-defined.js";

import { html } from "lit";

export type AttributeViewProps = ElementRest & {
    value: unknown;
    mode?: string;
    hideCopy?: boolean;
};

/**
 * @returns {TemplateResult} A Lit template result containing the configured ak-attribute-view
 *   element
 * @summary Helper function to create a AttributeView component programmatically
 *
 * @see {@link AttributeView} - The underlying web component
 */
export function akAttributeView(options: AttributeViewProps) {
    const { value, mode, hideCopy, ...rest } = options;

    return html`
        <ak-attribute-view
            ${spread(rest)}
            .value=${value}
            mode=${ifDefined(mode)}
            ?hideCopy=${hideCopy}
        ></ak-attribute-view>
    `;
}
