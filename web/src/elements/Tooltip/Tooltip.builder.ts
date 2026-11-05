/**
 * @file Function to generate default Tooltip instances
 */

import type { ElementRest } from "../types";
import type { Tooltip, Trigger } from "./Tooltip";

import { spread } from "@open-wc/lit-helpers";

import { html, TemplateResult } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

export type TooltipProps = ElementRest &
    Partial<Pick<Tooltip, "placement">> & {
        /** The element the tooltip describes; slotted into the default slot. */
        anchor: string | TemplateResult;
        content: string | TemplateResult;
        trigger?: Trigger;
        hideArrow?: boolean;
    };

/**
 * @returns {TemplateResult} A Lit template result containing the configured ak-tooltip element *
 * @summary Helper function to create a Tooltip component programmatically
 *
 * @see {@link Tooltip} - The underlying web component
 */
export function akTooltip(options: TooltipProps) {
    const { anchor, content, trigger, placement, hideArrow, ...rest } = options;

    return html`<ak-tooltip
        ${spread(rest)}
        trigger=${ifDefined(trigger)}
        placement=${ifDefined(placement)}
        ?hide-arrow=${!!hideArrow}
        >${anchor}<span slot="tooltip">${content}</span></ak-tooltip
    >`;
}
