import { LitFC } from "#elements/types";

import { spread } from "@open-wc/lit-helpers";
import type { LabelHTMLAttributes } from "react";

import { html, nothing } from "lit";
import { ifDefined } from "lit/directives/if-defined.js";

export interface FormLabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
    required?: boolean;
}

export const AKLabel: LitFC<FormLabelProps> = (
    { required, htmlFor, ...labelAttributes } = {},
    children,
) => {
    if (!children) return nothing;

    return html`<label
        class="pf-c-form__label"
        for=${ifDefined(htmlFor)}
        ?aria-required=${required}
        ${spread(labelAttributes)}
    >
        <span class="pf-c-form__label-text">${children}</span>
    </label>`;
};
