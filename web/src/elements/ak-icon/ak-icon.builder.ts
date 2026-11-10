import "./ak-icon.component.js";

import type { ElementRest } from "../types.js";
import { Icon } from "./ak-icon.component.js";

import { spread } from "@open-wc/lit-helpers";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

/* The `pick`ed fields here correspond to their types in the Icon class above. */

export type IconProps = ElementRest &
    Partial<Pick<Icon, "icon" | "family" | "fallback">> & {
        size?: string;
        variant?: string;
        effect?: string;
    };

/**
 * @summary Helper function to create an Icon component programmatically
 *
 * @returns {TemplateResult} A Lit template result containing the configured ak-icon element
 *
 * @see {@link Icon} - The underlying web component
 */
export function akIcon(options: IconProps = {}) {
    const { icon, family, fallback, size, variant, effect, ...rest } = options;
    return html`
        <ak-icon
            ${spread(rest)}
            icon=${ifDefined(icon)}
            family=${ifDefined(family)}
            fallback=${ifDefined(fallback)}
            size=${ifDefined(size)}
            variant=${ifDefined(variant)}
            effect=${ifDefined(effect)}
        ></ak-icon>
    `;
}
