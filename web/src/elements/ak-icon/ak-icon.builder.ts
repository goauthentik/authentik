import "./ak-icon.component.js";
import type { ElementRest } from "../types.js";
import { Icon } from "./ak-icon.component.js";

import { spread } from "@open-wc/lit-helpers";

import { html } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

export type IconProps = ElementRest & Partial<Pick<Icon, "name" | "label">>;

/**
 * @returns {TemplateResult} A Lit template result containing the configured ak-icon element
 * @summary Helper function to create an Icon component programmatically
 *
 * @see {@link Icon} - The underlying web component
 */
export function akIcon(options: IconProps = {}) {
    const { name, label, ...rest } = options;

    return html`<ak-icon
        ${spread(rest)}
        name=${ifDefined(name)}
        label=${ifDefined(label)}
    ></ak-icon>`;
}
