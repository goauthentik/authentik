import { type ElementRest } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

export type AttributeViewProps = ElementRest & {
    value: unknown;
    mode?: "json" | "yaml" | "tree";
    hideCopy?: boolean;
    showCount?: boolean;
};

/**
 * @returns {TemplateResult} A Lit template result containing the configured ak-attribute-view
 *   element
 * @summary Helper function to create a AttributeView component programmatically
 *
 * @see {@link AkAttributeView} - The underlying web component
 */
export function akAttributeView(options: AttributeViewProps) {
    const { value, mode, hideCopy, showCount, ...rest } = options;

    return html`
        <ak-attribute-view
            ${spread(rest)}
            .value=${value}
            mode=${ifDefined(mode)}
            ?hide-copy=${hideCopy}
            ?show-count=${showCount}
        ></ak-attribute-view>
    `;
}
