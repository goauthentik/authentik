import { LitFC } from "#elements/types";
import { ifPresent } from "#elements/utils/attributes";

import { spread } from "@open-wc/lit-helpers";
import type { LabelHTMLAttributes } from "react";

import { msg } from "@lit/localize";
import { html, nothing } from "lit";

export interface FormLabelProps extends LabelHTMLAttributes<HTMLLabelElement> {
    required?: boolean;
}

export const AKLabel: LitFC<FormLabelProps> = (
    { required, htmlFor, className, ...labelAttributes } = {},
    children,
) => {
    if (!children) return nothing;

    return html`<label
        class="pf-c-form__label ${className || ""}"
        for=${ifPresent(htmlFor)}
        aria-required=${required ? "true" : "false"}
        ${spread(labelAttributes)}
    >
        <span
            class="pf-c-form__label-text"
            data-required-label=${required ? msg("Required") : nothing}
            >${children}</span
        >
    </label>`;
};
