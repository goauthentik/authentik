import { LitFC } from "#elements/types";

import { msg } from "@lit/localize";
import { nothing } from "lit";

export interface FormLabelProps {
    "required"?: boolean;
    "htmlFor"?: string;
    "className"?: string;
    /**
     * Slot to project the label into, e.g. a form group's `label` slot.
     */
    "slot"?: string;
    "id"?: string;
    "aria-label"?: string;
}

export const AKLabel: LitFC<FormLabelProps> = (
    { required, htmlFor, className, slot, id, "aria-label": ariaLabel } = {},
    children,
) => {
    if (!children) return nothing;

    return (
        <label
            id={id}
            slot={slot}
            className={["pf-c-form__label", className]}
            htmlFor={htmlFor}
            aria-label={ariaLabel}
            aria-required={required ? "true" : "false"}
        >
            <span
                className="pf-c-form__label-text"
                data-required-label={required ? msg("Required") : nothing}
            >
                {children}
            </span>
        </label>
    );
};
