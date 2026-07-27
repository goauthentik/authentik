/**
 * @file Function to generate default Tooltip instances
 */

import { Tooltip, type Trigger } from "../Tooltip";
import type { ElementRest } from "../types";

import { spread } from "@open-wc/lit-helpers";

import { html, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

export type TooltipProps = ElementRest &
    Partial<Pick<Tooltip, "htmlFor" | "placement">> & {
        content: string | TemplateResult;
        trigger?: Trigger;
        hideArrow?: boolean;
    };

/**
 * @summary Helper function to create a Tooltip component programmatically
 *
 * @returns {TemplateResult} A Lit template result containing the configured ak-tooltip element
 *
 * @see {@link Tooltip} - The underlying web component
 */
export function akTooltip(options: TooltipProps) {
    const { content, htmlFor, trigger, placement, hideArrow, ...rest } = options;

    return html`
        <ak-tooltip
            ${spread(rest)}
            for=${ifDefined(htmlFor)}
            trigger=${ifDefined(trigger)}
            placement=${ifDefined(placement)}
            ?hide-arrow=${!!hideArrow}
            >${content}</ak-tooltip
        >
    `;
}
