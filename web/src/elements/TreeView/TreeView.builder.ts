import type { JsonValue } from "./TreeView.component";

import { type ElementRest } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

export type TreeViewProps = ElementRest & {
    value: JsonValue;
    summaryMaxLength?: number;
    summaryMaxCount?: number;
};

/**
 * @returns {TemplateResult} A Lit template result containing the configured ak-tree-view element
 * @summary Helper function to create a TreeView component programmatically
 *
 * @see {@link TreeView} - The underlying web component
 */
export function akTreeView(options: TreeViewProps) {
    const { value, summaryMaxLength, summaryMaxCount, ...rest } = options;

    return html`
        <ak-tree-view
            ${spread(rest)}
            .value=${value}
            summary-maxlength=${ifDefined(summaryMaxLength)}
            summary-maxcount=${ifDefined(summaryMaxCount)}
        ></ak-tree-view>
    `;
}
