import type { JsonValue } from "./StructuredView.component";

import { type ElementRest } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

export type StructuredViewProps = ElementRest & {
    value: JsonValue;
    summaryMaxLength?: number;
    summaryMaxCount?: number;
    showCount?: boolean;
};

/**
 * @returns {TemplateResult} A Lit template result containing the configured ak-structured-view
 *   element
 * @summary Helper function to create a StructuredView component programmatically
 *
 * @see {@link StructuredView} - The underlying web component
 */
export function akStructuredView(options: StructuredViewProps) {
    const { value, summaryMaxLength, summaryMaxCount, showCount, ...rest } = options;

    return html`
        <ak-structured-view
            ${spread(rest)}
            .value=${value}
            summary-maxlength=${ifDefined(summaryMaxLength)}
            summary-maxcount=${ifDefined(summaryMaxCount)}
            ?showCount=${Boolean(showCount)}
        ></ak-structured-view>
    `;
}
